#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
artifact=""; checksum=""; install_root="${RBF_INSTALL_ROOT:-/srv/rbf}"; env_source=""; target_environment="${RBF_TARGET_ENVIRONMENT:-test}"; no_backup=false; skip_backup=false; skip_host=false
usage() { echo "Usage: setup_website.sh [--artifact FILE --checksum FILE --install-root DIR --env FILE --target-environment test|production --no-backup --skip-host]" >&2; exit 2; }
if (($# == 0)); then
  [[ -t 0 && -t 1 ]] || { echo "[website] Without flags, setup_website.sh requires an interactive terminal." >&2; exit 2; }
  cat <<'BANNER'

Royal Blackwater Fleet – Configure Website Server
===================================================
This assistant atomically installs a verified release artifact.
Have the .tar.gz and .sha256 file transferred from the origin server ready.
An existing installation is backed up automatically before the update.

BANNER
  default_artifact="$(find "$SCRIPT_DIR" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -print -quit 2>/dev/null || true)"
  read -r -p "1/5 Release artifact [${default_artifact:-enter path}]: " answer
  artifact="${answer:-$default_artifact}"
  read -r -p "2/5 Checksum [${artifact}.sha256]: " checksum_answer
  checksum="${checksum_answer:-$artifact.sha256}"
  read -r -p "3/5 Installation root [${install_root}]: " root_answer
  [[ -z "$root_answer" ]] || install_root="$root_answer"
  read -r -p "4/5 Private environment file [generate automatically]: " env_source
  if [[ -L "$install_root/current" ]]; then
    echo "5/5 Existing installation detected; a coordinated backup will be created automatically."
  else
    read -r -p "5/5 First installation without an existing backup? [Y/n]: " backup_answer
    [[ -z "$backup_answer" || "${backup_answer,,}" =~ ^(y|yes)$ ]] && no_backup=true
  fi
fi
while (($#)); do
  case "$1" in
    --artifact) artifact="${2:-}"; shift 2;;
    --checksum) checksum="${2:-}"; shift 2;;
    --install-root) install_root="${2:-}"; shift 2;;
    --env) env_source="${2:-}"; shift 2;;
    --target-environment) target_environment="${2:-}"; shift 2;;
    --no-backup) no_backup=true; shift;;
    --skip-backup) skip_backup=true; shift;;
    --skip-host) skip_host=true; shift;;
    -h|--help) usage;; *) usage;;
  esac
done
[[ -n "$artifact" ]] || usage
[[ "$target_environment" =~ ^(test|production)$ ]] || { echo "[website] Invalid target environment: $target_environment" >&2; exit 2; }
artifact="$(realpath "$artifact")"; checksum="$(realpath "${checksum:-$artifact.sha256}")"
[[ -f "$artifact" && -f "$checksum" ]] || { echo "[website] Artifact or checksum is missing." >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || {
  sudo_args=(--artifact "$artifact" --checksum "$checksum" --install-root "$install_root" --target-environment "$target_environment")
  [[ -z "$env_source" ]] || sudo_args+=(--env "$env_source")
  [[ "$no_backup" == true ]] && sudo_args+=(--no-backup)
  [[ "$skip_backup" == true ]] && sudo_args+=(--skip-backup)
  [[ "$skip_host" == true ]] && sudo_args+=(--skip-host)
  exec sudo --preserve-env=RBF_INSTALL_ROOT bash "$0" "${sudo_args[@]}"
}
for command in flock python3 sha256sum systemctl; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "[website] Target host is not prepared: '$command' is missing." >&2
    echo "[website] This must first be configured on the website server (not the backup server)." >&2
    exit 1
  }
done
verifier="$SCRIPT_DIR/verify-artifact.py"
[[ -f "$verifier" ]] || { echo "[website] verify-artifact.py is missing next to setup_website.sh." >&2; exit 1; }
stage="$(mktemp -d /tmp/rbf-website-setup.XXXXXX)"; trap 'rm -rf "$stage"' EXIT
python3 "$verifier" "$artifact" "$stage/bundle" >/dev/null
installer="$stage/bundle/payload/infrastructure/scripts/release/install-artifact.sh"
[[ -x "$installer" ]] || { echo "[website] Release contains no installer." >&2; exit 1; }
host_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-host.sh"
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  [[ "$skip_host" == false ]] || { echo "[website] Docker/Compose is missing; --skip-host prevents automatic host preparation." >&2; exit 1; }
  [[ -x "$host_prepare" ]] || { echo "[website] Release contains no host bootstrap." >&2; exit 1; }
  echo "[website] Docker/Compose is missing. Installing the required host dependencies now."
  "$host_prepare"
fi
command -v docker >/dev/null 2>&1 || { echo "[website] Docker could not be installed." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[website] Docker Compose v2 is missing or unavailable." >&2; exit 1; }
legacy_install_root="/opt/rbf"
migration_helper="$stage/bundle/payload/infrastructure/scripts/release/migrate-install-root.sh"
if [[ ! -x "$migration_helper" && -x "$SCRIPT_DIR/migrate-install-root.sh" ]]; then
  migration_helper="$SCRIPT_DIR/migrate-install-root.sh"
fi
target_had_current=false
if [[ -e "$install_root/current" || -L "$install_root/current" ]]; then
  target_had_current=true
fi
if [[ "$install_root" == "/srv/rbf" && ( -e "$legacy_install_root" || -L "$legacy_install_root" ) ]]; then
  if [[ -e "$install_root" || -L "$install_root" ]]; then
    echo "[website] Old and new installation roots exist at the same time: $legacy_install_root and $install_root" >&2
    echo "[website] Automatic migration is being aborted for safety." >&2
    exit 1
  fi
  [[ -x "$migration_helper" ]] || { echo "[website] Release contains no installation-root migration helper." >&2; exit 1; }
  echo "[website] Automatically migrating the existing installation from $legacy_install_root to $install_root."
  "$migration_helper" "$legacy_install_root" "$install_root"
  target_had_current=true
fi
if [[ "$target_had_current" == false && "$no_backup" == false ]]; then
  shopt -s nullglob
  existing_releases=("$install_root/releases"/*)
  shopt -u nullglob
  if ((${#existing_releases[@]} > 0)); then
    echo "[website] No active installation, but releases exist under $install_root/releases." >&2
    echo "[website] Automatic first installation is being aborted for safety." >&2
    exit 1
  fi
  no_backup=true
  echo "[website] No existing installation found; first installation will continue without a pre-deployment backup."
fi
if [[ -z "$env_source" ]]; then
  env_source="$install_root/shared/.env"
  env_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-env.sh"
  [[ -x "$env_prepare" ]] || { echo "[website] Release contains no environment bootstrap." >&2; exit 1; }
  "$env_prepare" "$env_source" "$install_root/shared/first-run-credentials.txt" "$target_environment"
fi
[[ -f "$env_source" ]] || { echo "[website] Environment file is missing: $env_source" >&2; exit 1; }
source "$stage/bundle/payload/infrastructure/scripts/lib/env.sh"
export ENV_FILE="$env_source"
existing_environment="$(read_env DEPLOYMENT_ENVIRONMENT)"
if [[ -n "$existing_environment" && "$existing_environment" != "$target_environment" ]]; then
  die "Existing installation is marked as $existing_environment and cannot be repurposed as $target_environment. Use separate installation roots/servers."
fi
set_env_value DEPLOYMENT_ENVIRONMENT "$target_environment"
validate_env
tls_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-tls.sh"
[[ -x "$tls_prepare" ]] || { echo "[website] Release contains no TLS bootstrap." >&2; exit 1; }
"$tls_prepare" "$env_source" "$install_root/shared"
printf '\n[website] Verified. Preparing installation:\n  Artifact: %s\n  Target:   %s\n\n' "$artifact" "$install_root"
installer_args=(--artifact "$artifact" --checksum "$checksum" --install-root "$install_root" --requested-by origin)
[[ "$no_backup" == true ]] && installer_args+=(--no-backup)
[[ "$skip_backup" == true ]] && installer_args+=(--skip-backup)
[[ -z "$env_source" ]] || installer_args+=(--env "$env_source")
RBF_ARTIFACT_VERIFIER="$stage/bundle/payload/infrastructure/scripts/release/verify-artifact.py" \
  "$installer" "${installer_args[@]}"

credentials_file="$install_root/shared/first-run-credentials.txt"
if [[ -f "$credentials_file" && ! -L "$credentials_file" ]]; then
  printf '\n[website] First-run credentials (store securely once):\n'
  sed -n '1,20p' "$credentials_file"
  printf '[website] Then securely delete the credentials file: %s\n\n' "$credentials_file"
fi
