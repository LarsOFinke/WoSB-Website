#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
if [[ -f "${RBF_ARTIFACT_VERIFIER:-}" ]]; then
  VERIFIER="${RBF_ARTIFACT_VERIFIER}"
elif [[ -f "$SCRIPT_DIR/verify-artifact.py" ]]; then
  VERIFIER="$SCRIPT_DIR/verify-artifact.py"
elif [[ -f "$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py" ]]; then
  VERIFIER="$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py"
else
  echo "[release] Artifact verifier is missing." >&2
  exit 1
fi

artifact=""; checksum=""; install_root="${RBF_INSTALL_ROOT:-/srv/rbf}"
env_source=""; no_backup=false; skip_backup=false; requested_by="cli"; interactive_mode=false

usage() {
  cat >&2 <<'USAGE'
Usage: sudo install-artifact.sh --artifact FILE [options]
       Without flags, an interactive installation dialog opens in the terminal.

Options:
  --checksum FILE       Outer SHA-256 file (default: FILE.sha256)
  --install-root DIR    Versioned installation root (default: /srv/rbf)
  --env FILE            Private environment file (required on first install)
  --no-backup           Allow first install without a pre-deployment backup
  --skip-backup         Skip the coordinated pre-deployment backup for this activation
  --requested-by NAME   Operator recorded in deployment metadata
USAGE
  exit 2
}

interactive_setup() {
  [[ -t 0 && -t 1 ]] || { echo "[release] Without flags, install-artifact.sh requires an interactive terminal." >&2; exit 2; }
  local answer
  read -r -p "Release-Artefakt: " artifact
  [[ -n "$artifact" ]] || { echo "[release] A release artifact is required." >&2; exit 2; }
  read -r -p "Outer checksum [${artifact}.sha256]: " answer
  checksum="${answer:-${artifact}.sha256}"
  answer=""
  read -r -p "Installationsroot [${install_root}]: " answer
  [[ -z "$answer" ]] || install_root="$answer"
  answer=""
  read -r -p "Private environment file (required for first installation): " env_source
  answer=""
  read -r -p "Requested by [interactive]: " answer
  requested_by="${answer:-interactive}"
}

if (($# == 0)); then
  interactive_mode=true
  interactive_setup
fi

die() { echo "[release] $*" >&2; exit 1; }
require_command() { command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }

while (($#)); do
  case "$1" in
    --artifact) artifact="${2:-}"; shift 2 ;;
    --checksum) checksum="${2:-}"; shift 2 ;;
    --install-root) install_root="${2:-}"; shift 2 ;;
    --env) env_source="${2:-}"; shift 2 ;;
    --no-backup) no_backup=true; shift ;;
    --skip-backup) skip_backup=true; shift ;;
    --requested-by) requested_by="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[[ "$EUID" -eq 0 ]] || die "Artifact installation requires root."
for command in docker flock python3 sha256sum systemctl timeout; do require_command "$command"; done
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required."
[[ -n "$artifact" ]] || usage
artifact="$(realpath "$artifact")"
checksum="$(realpath "${checksum:-$artifact.sha256}")"
[[ -f "$artifact" && ! -L "$artifact" ]] || die "Artifact is missing or is a symbolic link: $artifact"
[[ -f "$checksum" && ! -L "$checksum" ]] || die "Checksum is missing or is a symbolic link: $checksum"
[[ "$install_root" == /* && "$install_root" != / ]] || die "Install root must be a specific absolute directory."
install_root="$(realpath -m "$install_root")"
if [[ -n "$env_source" ]]; then
  env_source="$(realpath "$env_source")"
  [[ -f "$env_source" && ! -L "$env_source" ]] || die "Environment file is missing or unsafe: $env_source"
fi

expected="$(awk 'NF {if (++lines != 1 || $1 !~ /^[0-9a-fA-F]{64}$/) exit 2; print tolower($1)} END {if (lines != 1) exit 2}' "$checksum")" \
  || die "Checksum file must contain exactly one SHA-256 record."
actual="$(sha256sum "$artifact" | awk '{print $1}')"
[[ "$actual" == "$expected" ]] || die "Outer artifact checksum mismatch."

shared="$install_root/shared"
releases="$install_root/releases"
install -d -m 0750 "$install_root" "$shared" "$releases" "$shared/data"
install -d -m 0700 "$shared/locks" "$shared/deployments" "$shared/release-artifacts" "$shared/releases/inbox"
exec 9>"$shared/locks/release.lock"; flock 9

stage="$(mktemp -d "$releases/.incoming.XXXXXX")"
previous_release=""; previous_env=""; switched=false; backup_postgres=""; backup_files=""
deployment_record=""; artifact_copy=""
cleanup() { rm -rf "$stage"; }
trap cleanup EXIT

manifest_json="$(python3 "$VERIFIER" "$artifact" "$stage/bundle")"
version="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["version"])' "$manifest_json")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Manifest version is not SemVer: $version"
release_dir="$releases/$version"
if [[ -e "$release_dir" ]]; then
  current_target="$(readlink -f "$install_root/current" 2>/dev/null || true)"
  [[ "$current_target" != "$release_dir" ]] || die "Immutable release already exists and is active: $release_dir"
  deployment_record_candidate="$shared/deployments/$version.json"
  deployment_state=""
  if [[ -f "$deployment_record_candidate" ]]; then
    deployment_state="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("state", ""))' "$deployment_record_candidate" 2>/dev/null || true)"
  fi
  [[ "$deployment_state" == failed || "$deployment_state" == activating ]] \
    || die "Immutable release already exists: $release_dir"
  echo "[release] Bereinige verwaisten Release-Versuch $release_dir (Status: $deployment_state)."
  rm -rf -- "$release_dir"
fi

if [[ -L "$install_root/current" ]]; then
  previous_release="$(readlink -f "$install_root/current")"
  [[ "$previous_release" == "$releases/"* && -d "$previous_release" ]] \
    || die "Current release link escapes the release root."
elif [[ -e "$install_root/current" ]]; then
  die "Current installation entry is not a symbolic link."
fi

if [[ "$interactive_mode" == true && -z "$previous_release" ]]; then
  read -r -p "No active installation found. Continue as a first installation without a backup? [y/N]: " answer
  case "${answer,,}" in
    y|yes) no_backup=true ;;
    *) die "First installation aborted; a backup is not possible here." ;;
  esac
fi

if [[ -n "$previous_release" && "$no_backup" == true ]]; then
  die "--no-backup is permitted only for a genuinely new installation."
fi
if [[ -z "$previous_release" && "$no_backup" != true ]]; then
  die "First installation requires explicit --no-backup."
fi
if [[ -z "$env_source" && ! -f "$shared/.env" ]]; then
  die "First installation requires --env FILE."
fi

if [[ -n "$previous_release" && "$skip_backup" != true ]]; then
  postgres_result="$stage/postgres.result"; files_result="$stage/files.result"; set_result="$stage/set.result"
  verification_result="$stage/verification.result"; recovery_result="$stage/recovery.result"
  backup_runner="$SCRIPT_DIR/../backup/run-consistent-backup.sh"
  [[ -x "$backup_runner" ]] || die "Incoming release has no coordinated backup runner."
  RBF_INSTALL_ROOT="$install_root" RBF_RUNTIME_INFRA_DIR="$previous_release/infrastructure" \
    "$backup_runner" \
    --reason pre-deployment --postgres-result "$postgres_result" --files-result "$files_result" \
    --verification-result "$verification_result" --recovery-result "$recovery_result" \
    --backup-set-result "$set_result"
  backup_postgres="$(cat "$postgres_result")"
  backup_files="$(cat "$files_result")"
  [[ -f "$backup_postgres" && -f "$backup_files" && -s "$set_result" ]] \
    || die "Coordinated pre-deployment backup did not return all required artifacts."
fi
[[ "$skip_backup" != true ]] || echo "[release] Coordinated pre-deployment backup is disabled for this run."

rollback_failed_install() {
  local code=$?
  trap - ERR
  set +e
  failure_log="$shared/deployments/failed-${version}-$(date -u +%Y%m%dT%H%M%SZ).log"
  {
    echo "Royal Blackwater Fleet release activation failed"
    echo "version=$version"
    echo "release=$release_dir"
    echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    if [[ -d "$release_dir/infrastructure" ]]; then
      failed_compose=(docker compose --env-file "$shared/.env" --env-file "$release_dir/infrastructure/.release.env" -f "$release_dir/infrastructure/compose.release.yml")
      (cd "$release_dir/infrastructure" && "${failed_compose[@]}" ps -a) || true
      (cd "$release_dir/infrastructure" && "${failed_compose[@]}" logs --tail=240 api gateway postgres) || true
    fi
    journalctl -u rbf-hub.service -n 240 --no-pager || true
  } > "$failure_log" 2>&1 || true
  chmod 0600 "$failure_log" 2>/dev/null || true
  echo "[release] Activation diagnostics were saved: $failure_log" >&2
  if [[ "$switched" == true ]]; then
    if [[ -n "$previous_release" ]]; then
      ln -sfn "$previous_release" "$install_root/.current.rollback"
      mv -Tf "$install_root/.current.rollback" "$install_root/current"
      [[ -z "$previous_env" || ! -f "$previous_env" ]] || install -m 0600 "$previous_env" "$shared/.env"
      RBF_SYSTEMD_INFRA_DIR="$install_root/current/infrastructure" \
        "$install_root/current/infrastructure/scripts/deployment/install-systemd.sh"
      systemctl restart rbf-hub.service
      if [[ -n "$backup_files" ]]; then
        "$install_root/current/infrastructure/scripts/backup/restore-data.sh" --yes "$backup_files"
      fi
      if [[ -n "$backup_postgres" ]]; then
        RBF_UPDATE_LOCK_HELD=true "$install_root/current/infrastructure/scripts/backup/restore-postgres.sh" "$backup_postgres"
      fi
    else
      "$release_dir/infrastructure/scripts/services/stop.sh" || true
      rm -f "$install_root/current"
    fi
  elif [[ -n "$previous_env" && -f "$previous_env" ]]; then
    install -m 0600 "$previous_env" "$shared/.env"
  fi
  if [[ -d "$release_dir" && "$(readlink -f "$install_root/current" 2>/dev/null || true)" != "$release_dir" ]]; then
    rm -rf -- "$release_dir"
  fi
  if [[ -n "$artifact_copy" ]]; then rm -f -- "$artifact_copy" "$artifact_copy.sha256"; fi
  [[ -z "$deployment_record" || ! -f "$deployment_record" ]] || \
    python3 -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); d=json.loads(p.read_text()); d["state"]="failed"; p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); p.chmod(0o600)' "$deployment_record"
  echo "[release] Activation failed; previous release and coordinated backup were restored where available." >&2
  exit "$code"
}
trap rollback_failed_install ERR

# Block manual restore/update operations only after the preflight backup has
# released its own update lock.
install -d -m 0700 "$shared/data/control/run"
exec 8>"$shared/data/control/run/update.lock"; flock 8

if [[ -f "$shared/.env" ]]; then
  previous_env="$shared/deployments/$version.env.before"
  install -m 0600 "$shared/.env" "$previous_env"
fi
if [[ -n "$env_source" ]]; then
  env_target="$shared/.env"
  if [[ "$(realpath -m "$env_source")" != "$(realpath -m "$env_target")" ]]; then
    install -m 0600 "$env_source" "$env_target"
  else
    chmod 0600 "$env_target"
  fi
fi

mv "$stage/bundle/payload" "$release_dir"
install -m 0644 "$stage/bundle/manifest.json" "$release_dir/.release-manifest.json"
install -m 0644 "$stage/bundle/SHA256SUMS" "$release_dir/.release-SHA256SUMS"
ln -s "$shared/.env" "$release_dir/infrastructure/.env"
ln -s "$shared/data" "$release_dir/infrastructure/data"
safe_tag="${version//[^0-9A-Za-z_.-]/-}"
cat > "$release_dir/infrastructure/.release.env" <<ENV
RBF_API_IMAGE=rbf-hub-api:${safe_tag}
RBF_GATEWAY_IMAGE=rbf-hub-gateway:${safe_tag}
ENV
chmod 0644 "$release_dir/infrastructure/.release.env"

RBF_INSTALL_ROOT="$install_root" RBF_COMPOSE_FILE="$release_dir/infrastructure/compose.release.yml" \
  bash -c 'source "$1/scripts/lib/env.sh"; validate_env; source "$1/scripts/lib/host/storage.sh"; prepare_data_directories' \
  _ "$release_dir/infrastructure"

compose=(docker compose --env-file "$shared/.env" --env-file "$release_dir/infrastructure/.release.env" \
  -f "$release_dir/infrastructure/compose.release.yml")
(cd "$release_dir/infrastructure" && "${compose[@]}" build api gateway)

artifact_copy="$shared/release-artifacts/rbf-deployment-$version.tar.gz"
install -m 0600 "$artifact" "$artifact_copy"
(cd "$(dirname "$artifact_copy")" && sha256sum "$(basename "$artifact_copy")" > "$(basename "$artifact_copy").sha256")
chmod 0600 "$artifact_copy.sha256"

deployment_record="$shared/deployments/$version.json"
CURRENT="$release_dir" PREVIOUS="$previous_release" POSTGRES="$backup_postgres" FILES="$backup_files" \
ENV_BACKUP="$previous_env" ARTIFACT="$artifact_copy" REQUESTED_BY="$requested_by" RECORD="$deployment_record" \
python3 <<'PY'
import json, os
from datetime import datetime, timezone
from pathlib import Path
record = Path(os.environ["RECORD"])
payload = {
    "schema_version": 1,
    "state": "activating",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "requested_by": os.environ["REQUESTED_BY"],
    "current_release": os.environ["CURRENT"],
    "previous_release": os.environ["PREVIOUS"] or None,
    "rollback_postgres": os.environ["POSTGRES"] or None,
    "rollback_files": os.environ["FILES"] or None,
    "previous_environment": os.environ["ENV_BACKUP"] or None,
    "release_artifact": os.environ["ARTIFACT"],
}
temporary = record.with_name("." + record.name + ".tmp")
temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
temporary.replace(record)
record.chmod(0o600)
PY

ln -sfn "$release_dir" "$install_root/.current.next"
mv -Tf "$install_root/.current.next" "$install_root/current"
switched=true
RBF_SYSTEMD_INFRA_DIR="$install_root/current/infrastructure" \
  "$install_root/current/infrastructure/scripts/deployment/install-systemd.sh"
echo "[release] Restarting rbf-hub.service and waiting for Spring Boot/Compose."
timeout 120s systemctl restart rbf-hub.service
echo "[release] Running readiness and gateway smoke tests (max. 60 seconds)."
smoke_args=()
[[ -z "$previous_release" ]] && smoke_args+=(--bootstrap-login)
timeout 60s "$install_root/current/infrastructure/scripts/checks/smoke-test.sh" "${smoke_args[@]}"

if [[ "$(awk -F= '$1 == "DEPLOYMENT_ENVIRONMENT" {gsub(/^\047|\047$/, "", $2); gsub(/^"|"$/, "", $2); print $2; exit}' "$shared/.env")" == production ]]; then
  echo "[release] Finalize public production TLS within the atomic activation."
  RBF_RUNTIME_INFRA_DIR="$install_root/current/infrastructure" /usr/bin/env bash -c '
    set -Eeuo pipefail
    source "$1/scripts/lib/env.sh"
    source "$1/scripts/lib/host/tls.sh"
    configure_production_tls
    [[ "$(read_env CERTIFICATE_PROVIDER)" == letsencrypt ]] || die "Production TLS was not activated."
    "$1/scripts/checks/smoke-test.sh"
  ' _ "$install_root/current/infrastructure"
fi

install -m 0600 "$artifact_copy" "$shared/release-artifacts/current.tar.gz"
(cd "$shared/release-artifacts" && sha256sum current.tar.gz > current.tar.gz.sha256)
printf '%s\n' "$version" > "$shared/current-version"
chmod 0644 "$shared/current-version"
python3 -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); d=json.loads(p.read_text()); d["state"]="active"; p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); p.chmod(0o600)' "$deployment_record"
install -m 0600 "$deployment_record" "$shared/deployment-state.json"
trap - ERR
echo "[release] Activated Royal Blackwater Fleet $version from a verified compiled artifact."
