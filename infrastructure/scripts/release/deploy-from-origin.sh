#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=../lib/origin-target.sh
source "$SCRIPT_DIR/../lib/origin-target.sh"
rbf_origin_select_target "$ROOT_DIR" "$@"
target_environment="$RBF_ORIGIN_TARGET"; config_file="$RBF_ORIGIN_CONFIG_FILE"
origin_prefix="[origin:$target_environment]"
if [[ "$EUID" -eq 0 && -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
  echo "$origin_prefix Note: deploy.sh does not require local sudo; run the transfer as $SUDO_USER." >&2
  user_group="$(id -gn "$SUDO_USER")"
  if [[ -f "$config_file" ]]; then
    chown "$SUDO_USER:$user_group" "$config_file"
    chmod 0600 "$config_file"
  fi
  # Previous sudo builds can leave unreadable Maven/Vite output behind. These
  # paths are generated artifacts, so repairing their ownership is safe and
  # keeps the actual build in the invoking user's environment.
  for generated in "$ROOT_DIR/spring-api/target" "$ROOT_DIR/frontend/dist" "$ROOT_DIR/release"; do
    [[ -e "$generated" ]] || continue
    chown -R "$SUDO_USER:$user_group" "$generated"
  done
  exec sudo -u "$SUDO_USER" -H -- bash "$0" "$@"
fi
artifact=""; host=""; user=""; bootstrap_user=""; bootstrap_identity_file=""; port=""; remote_dir=""; identity_file=""; source_revision=""; env_source=""; install_root=""; app_hostname=""; letsencrypt_email=""; no_backup=false; automated=false
interactive=false; configure=false
usage(){ echo "Usage: deploy.sh|update.sh [--test|--production] [--configure] [--artifact FILE] [--host HOST] [--user USER] [--bootstrap-user USER] [--bootstrap-identity-file FILE] [--identity-file FILE] [--port PORT] [--remote-dir DIR] [--config FILE]" >&2; exit 2; }
discover_identity_file() {
  [[ -n "$identity_file" ]] && return 0
  [[ -n "${HOME:-}" && -n "$user" ]] || return 0
  local candidate
  for candidate in "$(rbf_origin_default_identity_path "$target_environment" "$user")" "$HOME/.ssh/$user"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      identity_file="$candidate"
      return 0
    fi
  done
}
configure_deploy_identity() {
  local answer suggested
  suggested="$(rbf_origin_configure_identity_suggestion \
    "$ROOT_DIR" "$identity_file" "$target_environment" "$user")"
  read -r -p "SSH identity outside the repository for $user [${suggested}]: " answer
  identity_file="$(rbf_origin_resolve_identity_path "${answer:-$suggested}")"
  rbf_origin_require_external_identity "$ROOT_DIR" "$identity_file" "Deployment SSH identity"
  if [[ -n "$identity_file" && ! -f "$identity_file" ]]; then
    read -r -p "Deploy key is missing. Generate a dedicated Ed25519 key without a passphrase now? [Y/n]: " answer
    case "${answer,,}" in
      ""|y|yes)
        command -v ssh-keygen >/dev/null 2>&1 || { echo "[origin] ssh-keygen is missing on the origin machine." >&2; exit 1; }
        install -d -m 0700 "$(dirname "$identity_file")"
        ssh-keygen -q -t ed25519 -a 100 -N "" -C "rbf-deployment-$user@$host" -f "$identity_file"
        chmod 0600 "$identity_file"
        chmod 0644 "$identity_file.pub"
        echo "[origin] Dedicated deploy key was generated: $identity_file"
        ;;
      *) identity_file="" ;;
    esac
  fi
}
configure_bootstrap_access() {
  local answer
  read -r -p "Initial SSH user for a fresh target server (blank = not required): " answer
  bootstrap_user="$answer"
  [[ -n "$bootstrap_user" ]] || return 0
  [[ "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] \
    || { echo "[origin] Invalid bootstrap username: $bootstrap_user" >&2; exit 2; }
  read -r -p "External identity for $bootstrap_user (blank = SSH configuration/agent/password): " answer
  bootstrap_identity_file="$answer"
  if [[ -n "$bootstrap_identity_file" ]]; then
    bootstrap_identity_file="$(rbf_origin_resolve_identity_path "$bootstrap_identity_file")"
    rbf_origin_require_external_identity "$ROOT_DIR" "$bootstrap_identity_file" "Bootstrap SSH identity"
  fi
}
initial_argument_count=$#
while (($#)); do case "$1" in
  --test|--production) shift;;
  --configure) configure=true; shift;;
  --artifact) artifact="${2:-}"; automated=true; shift 2;; --host) host="${2:-}"; shift 2;; --user) user="${2:-}"; shift 2;;
  --bootstrap-user) bootstrap_user="${2:-}"; shift 2;;
  --bootstrap-identity-file) bootstrap_identity_file="${2:-}"; shift 2;;
  --port) port="${2:-}"; shift 2;; --remote-dir) remote_dir="${2:-}"; shift 2;;
  --identity-file) identity_file="${2:-}"; shift 2;;
  --source-revision) source_revision="${2:-}"; shift 2;; --env) env_source="${2:-}"; automated=true; shift 2;;
  --install-root) install_root="${2:-}"; automated=true; shift 2;; --no-backup) no_backup=true; automated=true; shift;;
  --config) config_file="${2:-}"; shift 2;;
  -h|--help) usage;; *) usage;; esac; done
if [[ -e "$config_file" ]]; then
  [[ -f "$config_file" && ! -L "$config_file" ]] || { echo "$origin_prefix Origin configuration must be a regular, non-symlink file: $config_file" >&2; exit 1; }
  config_mode="$(stat -c '%a' "$config_file")"
  [[ "$config_mode" == 600 ]] || { echo "$origin_prefix Unsafe permissions on $config_file ($config_mode); expected 600." >&2; exit 1; }
  config_owner="$(stat -c '%u' "$config_file")"
  [[ "$config_owner" == "$(id -u)" ]] || { echo "$origin_prefix Origin configuration is not owned by the invoking user." >&2; exit 1; }
  # shellcheck disable=SC1090
  source "$config_file"
  host="${host:-${RBF_DEPLOY_HOST:-}}"; user="${user:-${RBF_DEPLOY_USER:-rbfadmin}}"
  port="${port:-${RBF_DEPLOY_PORT:-22}}"; remote_dir="${remote_dir:-${RBF_DEPLOY_REMOTE_DIR:-/tmp/rbf-release}}"
  identity_file="${identity_file:-${RBF_DEPLOY_IDENTITY_FILE:-}}"
  install_root="${install_root:-${RBF_DEPLOY_INSTALL_ROOT:-}}"; env_source="${env_source:-${RBF_DEPLOY_ENV_SOURCE:-}}"
  app_hostname="${app_hostname:-${RBF_DEPLOY_APP_HOSTNAME:-}}"; letsencrypt_email="${letsencrypt_email:-${RBF_DEPLOY_LETSENCRYPT_EMAIL:-}}"
fi
port="${port:-22}"; remote_dir="${remote_dir:-/tmp/rbf-release}"
if [[ "$configure" == true || ( "$target_environment" == test && "$initial_argument_count" -eq 0 && ! -f "$config_file" ) ]]; then
  interactive=true
elif [[ ! -f "$config_file" && -z "$host" ]]; then
  echo "$origin_prefix Origin configuration is missing: $config_file" >&2
  if [[ "$target_environment" == production ]]; then
    echo "$origin_prefix Production is configured only after an explicit './deploy.sh --production --configure'." >&2
  else
    echo "$origin_prefix Configure the target with './deploy.sh --configure'." >&2
  fi
  exit 1
fi
if [[ "$interactive" == true ]]; then
  [[ -t 0 && -t 1 ]] || { echo "[origin] Without flags, deploy requires an interactive terminal." >&2; exit 2; }
  read -r -p "Webseitenserver [${host}]: " answer; host="${answer:-$host}"
  read -r -p "SSH user [${user:-rbfadmin}]: " answer; user="${answer:-${user:-rbfadmin}}"
  configure_deploy_identity
  configure_bootstrap_access
  read -r -p "SSH-Port [${port:-22}]: " answer; port="${answer:-${port:-22}}"
  read -r -p "Remote-Arbeitsverzeichnis [${remote_dir}]: " answer; remote_dir="${answer:-$remote_dir}"
  read -r -p "Vorhandenes Artefakt (leer = neu bauen): " artifact
  read -r -p "Quellrevision [HEAD]: " source_revision
  if [[ "$target_environment" == production ]]; then
    read -r -p "Öffentlicher Produktions-DNS-Name [${app_hostname}]: " answer; app_hostname="${answer:-$app_hostname}"
    read -r -p "Let's-Encrypt-Kontakt-E-Mail [${letsencrypt_email}]: " answer; letsencrypt_email="${answer:-$letsencrypt_email}"
    [[ -n "$app_hostname" && -n "$letsencrypt_email" ]] || { echo "[origin] Production DNS name and Let's Encrypt email are required." >&2; exit 2; }
  fi
fi
[[ -n "$host" ]] || usage; user="${user:-rbfadmin}"
discover_identity_file
if [[ -n "$identity_file" ]]; then
  identity_file="$(rbf_origin_resolve_identity_path "$identity_file")"
  rbf_origin_require_external_identity "$ROOT_DIR" "$identity_file" "Deployment SSH identity"
fi
if [[ -n "$bootstrap_identity_file" ]]; then
  bootstrap_identity_file="$(rbf_origin_resolve_identity_path "$bootstrap_identity_file")"
  rbf_origin_require_external_identity "$ROOT_DIR" "$bootstrap_identity_file" "Bootstrap SSH identity"
fi
[[ "$user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo "[origin] Invalid SSH username: $user" >&2; exit 2; }
[[ -z "$bootstrap_user" || "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo "[origin] Invalid bootstrap username: $bootstrap_user" >&2; exit 2; }
[[ -z "$bootstrap_identity_file" || -f "$bootstrap_identity_file" ]] || { echo "[origin] Bootstrap identity file is missing: $bootstrap_identity_file" >&2; exit 2; }
[[ "$port" =~ ^[0-9]+$ && "$port" -le 65535 ]] || { echo "[origin] Invalid SSH port: $port" >&2; exit 2; }
[[ "$remote_dir" == /* ]] || { echo "[origin] Remote working directory must be absolute: $remote_dir" >&2; exit 2; }
if [[ "$interactive" == true ]]; then
  umask 077; temporary="${config_file}.tmp.$$"
  install -d -m 0700 "$(dirname "$config_file")"
  cat > "$temporary" <<EOF
RBF_DEPLOY_HOST=$(printf '%q' "$host")
RBF_DEPLOY_USER=$(printf '%q' "$user")
RBF_DEPLOY_PORT=$(printf '%q' "$port")
RBF_DEPLOY_REMOTE_DIR=$(printf '%q' "$remote_dir")
RBF_DEPLOY_IDENTITY_FILE=$(printf '%q' "$identity_file")
RBF_DEPLOY_INSTALL_ROOT=$(printf '%q' "$install_root")
RBF_DEPLOY_ENV_SOURCE=$(printf '%q' "$env_source")
RBF_DEPLOY_APP_HOSTNAME=$(printf '%q' "$app_hostname")
RBF_DEPLOY_LETSENCRYPT_EMAIL=$(printf '%q' "$letsencrypt_email")
EOF
  mv -f "$temporary" "$config_file"
  chmod 0600 "$config_file"
fi
[[ "$EUID" -ne 0 ]] || echo "$origin_prefix Note: deploy.sh does not require local sudo." >&2
[[ -z "$identity_file" || -f "$identity_file" ]] || { echo "[origin] SSH identity file is missing: $identity_file" >&2; exit 1; }
ssh_args=(-o BatchMode=yes -o IdentitiesOnly=yes -p "$port")
scp_args=(-o BatchMode=yes -o IdentitiesOnly=yes -P "$port")
if [[ -n "$identity_file" ]]; then
  ssh_args+=(-i "$identity_file")
  scp_args+=(-i "$identity_file")
fi
identity_label="${identity_file:-SSH-Agent}"
echo "$origin_prefix Target profile=$target_environment Configuration=$config_file"
[[ "$target_environment" != production ]] || echo "$origin_prefix PRODUCTION target explicitly selected."
echo "$origin_prefix Checking key access: $user@$host:$port (identity: $identity_label)."
bootstrap_deploy_access() (
  set -Eeuo pipefail
  [[ -n "$identity_file" ]] || { echo "[origin] Bootstrap requires a fixed private identity file." >&2; exit 1; }
  command -v ssh-keygen >/dev/null 2>&1 || { echo "[origin] ssh-keygen is missing on the origin machine." >&2; exit 1; }
  local control_dir remote_bootstrap public_key_file generated_public_key=false connection_established=false
  control_dir="$(mktemp -d /tmp/rbf-origin-bootstrap.XXXXXX)"
  remote_bootstrap="/tmp/rbf-ssh-bootstrap-$$"
  public_key_file="${identity_file}.pub"
  if [[ ! -f "$public_key_file" ]]; then
    public_key_file="$control_dir/rbfadmin.pub"
    ssh-keygen -y -f "$identity_file" > "$public_key_file"
    chmod 0600 "$public_key_file"
    generated_public_key=true
  fi
  bootstrap_ssh_args=(-p "$port" -o ControlMaster=auto -o ControlPersist=30s -o "ControlPath=$control_dir/control-%C")
  bootstrap_scp_args=(-P "$port" -o ControlMaster=auto -o ControlPersist=30s -o "ControlPath=$control_dir/control-%C")
  if [[ -n "$bootstrap_identity_file" ]]; then
    bootstrap_ssh_args+=(-o IdentitiesOnly=yes -o BatchMode=yes -i "$bootstrap_identity_file")
    bootstrap_scp_args+=(-o IdentitiesOnly=yes -o BatchMode=yes -i "$bootstrap_identity_file")
  fi
  cleanup_bootstrap() {
    if [[ "$connection_established" == true ]]; then
      cleanup_bootstrap_command=(rm -rf -- "$remote_bootstrap")
      cleanup_bootstrap_line=""; for word in "${cleanup_bootstrap_command[@]}"; do printf -v quoted ' %q' "$word"; cleanup_bootstrap_line+="$quoted"; done
      ssh "${bootstrap_ssh_args[@]}" "$bootstrap_user@$host" "$cleanup_bootstrap_line" >/dev/null 2>&1 || true
      ssh "${bootstrap_ssh_args[@]}" -O exit "$bootstrap_user@$host" >/dev/null 2>&1 || true
    fi
    rm -rf -- "$control_dir"
  }
  trap cleanup_bootstrap EXIT

  bootstrap_dirs=(mkdir -p "$remote_bootstrap/infrastructure/scripts/setup" "$remote_bootstrap/infrastructure/scripts/lib")
  bootstrap_dirs_line=""; for word in "${bootstrap_dirs[@]}"; do printf -v quoted ' %q' "$word"; bootstrap_dirs_line+="$quoted"; done
  bootstrap_auth_label="${bootstrap_identity_file:-SSH configuration/agent or password}"
  echo "[origin] Configuring $user once through $bootstrap_user@$host (authentication: $bootstrap_auth_label)."
  ssh "${bootstrap_ssh_args[@]}" "$bootstrap_user@$host" "$bootstrap_dirs_line"
  connection_established=true
  scp "${bootstrap_scp_args[@]}" \
    "$ROOT_DIR/infrastructure/scripts/setup/provision-ssh-admin.sh" \
    "$bootstrap_user@$host:$remote_bootstrap/infrastructure/scripts/setup/"
  scp "${bootstrap_scp_args[@]}" \
    "$ROOT_DIR/infrastructure/scripts/lib/common.sh" \
    "$bootstrap_user@$host:$remote_bootstrap/infrastructure/scripts/lib/"
  scp "${bootstrap_scp_args[@]}" "$public_key_file" "$bootstrap_user@$host:$remote_bootstrap/rbfadmin.pub"
  if [[ "$bootstrap_user" == root ]]; then
    bootstrap_command=(bash "$remote_bootstrap/infrastructure/scripts/setup/provision-ssh-admin.sh" "$user" "$remote_bootstrap/rbfadmin.pub")
  else
    bootstrap_command=(sudo bash "$remote_bootstrap/infrastructure/scripts/setup/provision-ssh-admin.sh" "$user" "$remote_bootstrap/rbfadmin.pub")
  fi
  bootstrap_line=""; for word in "${bootstrap_command[@]}"; do printf -v quoted ' %q' "$word"; bootstrap_line+="$quoted"; done
  ssh -t "${bootstrap_ssh_args[@]}" "$bootstrap_user@$host" "$bootstrap_line"
  [[ "$generated_public_key" == false ]] || echo "[origin] Public key was derived temporarily from the private identity."
)

if ! ssh "${ssh_args[@]}" "$user@$host" "sudo -n /usr/bin/true"; then
  if [[ -z "$bootstrap_user" && -t 0 && -t 1 ]]; then
    read -r -p "Initial SSH user for the one-time rbfadmin setup: " bootstrap_user
    read -r -p "External identity for $bootstrap_user (blank = SSH configuration/agent/password): " bootstrap_identity_file
    if [[ -n "$bootstrap_identity_file" ]]; then
      bootstrap_identity_file="$(rbf_origin_resolve_identity_path "$bootstrap_identity_file")"
      rbf_origin_require_external_identity "$ROOT_DIR" "$bootstrap_identity_file" "Bootstrap SSH identity"
    fi
  fi
  [[ "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] \
    || { echo "[origin] Key access is missing; --bootstrap-user USER is required." >&2; exit 1; }
  [[ -z "$bootstrap_identity_file" || -f "$bootstrap_identity_file" ]] \
    || { echo "[origin] Bootstrap identity file is missing: $bootstrap_identity_file" >&2; exit 1; }
  bootstrap_deploy_access
  echo "[origin] Checking the newly configured key access."
  ssh "${ssh_args[@]}" "$user@$host" "sudo -n /usr/bin/true" \
    || { echo "[origin] rbfadmin was provisioned, but key-only access is still not operational." >&2; exit 1; }
fi
if [[ -z "$artifact" ]]; then
  args=(--output-dir "$ROOT_DIR/release"); [[ -z "$source_revision" ]] || args+=(--source-revision "$source_revision")
  "$SCRIPT_DIR/build-artifact.sh" "${args[@]}"
  artifact="$(find "$ROOT_DIR/release" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
fi
artifact="$(realpath "$artifact")"; checksum="$artifact.sha256"
[[ -f "$artifact" && -f "$checksum" ]] || { echo "[origin] Artifact or checksum is missing." >&2; exit 1; }
cleanup_remote_stage() {
  cleanup_command=(rm -f -- "$remote_dir/$(basename "$artifact")" "$remote_dir/$(basename "$checksum")" "$remote_dir/setup_website.sh" "$remote_dir/migrate-install-root.sh" "$remote_dir/cleanup-failed-release.sh" "$remote_dir/verify-artifact.py")
  cleanup_line=""; for word in "${cleanup_command[@]}"; do printf -v quoted ' %q' "$word"; cleanup_line+="$quoted"; done
  ssh "${ssh_args[@]}" "$user@$host" "$cleanup_line" \
    >/dev/null 2>&1 || echo "[origin] Remote staging could not be cleaned up: $remote_dir" >&2
}
trap cleanup_remote_stage EXIT
mkdir_line=""; printf -v quoted ' %q' mkdir; mkdir_line+="$quoted"; printf -v quoted ' %q' -p; mkdir_line+="$quoted"; printf -v quoted ' %q' "$remote_dir"; mkdir_line+="$quoted"
ssh "${ssh_args[@]}" "$user@$host" "$mkdir_line"
scp "${scp_args[@]}" "$artifact" "$checksum" \
  "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh" \
  "$ROOT_DIR/infrastructure/scripts/release/migrate-install-root.sh" \
  "$ROOT_DIR/infrastructure/scripts/release/cleanup-failed-release.sh" \
  "$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py" "$user@$host:$remote_dir/"
cleanup_command=(sudo -n bash "$remote_dir/cleanup-failed-release.sh" --if-present --yes)
[[ -z "$install_root" ]] || cleanup_command+=(--install-root "$install_root")
cleanup_line=""; for word in "${cleanup_command[@]}"; do printf -v quoted ' %q' "$word"; cleanup_line+="$quoted"; done
echo "$origin_prefix Cleaning up failed inactive releases on the target server (if present)."
ssh "${ssh_args[@]}" "$user@$host" "$cleanup_line"
remote_command=(sudo -n bash "$remote_dir/setup_website.sh" --target-environment "$target_environment")
remote_command+=(--artifact "$remote_dir/$(basename "$artifact")" --checksum "$remote_dir/$(basename "$checksum")")
[[ -z "$app_hostname" ]] || remote_command+=(--hostname "$app_hostname")
[[ -z "$letsencrypt_email" ]] || remote_command+=(--letsencrypt-email "$letsencrypt_email")
if [[ "$automated" == true ]]; then
  [[ -z "$install_root" ]] || remote_command+=(--install-root "$install_root")
  [[ -z "$env_source" ]] || remote_command+=(--env "$env_source")
  [[ "$no_backup" == true ]] && remote_command+=(--no-backup)
fi
remote_line=""; for word in "${remote_command[@]}"; do printf -v quoted ' %q' "$word"; remote_line+="$quoted"; done
ssh "${ssh_args[@]}" "$user@$host" "$remote_line"
