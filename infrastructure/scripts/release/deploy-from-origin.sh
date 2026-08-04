#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
config_file="${RBF_ORIGIN_CONFIG:-$ROOT_DIR/.env.origin}"
if [[ "$EUID" -eq 0 && -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
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
artifact=""; host=""; user=""; port="22"; remote_dir="/tmp/rbf-release"; source_revision=""; env_source=""; install_root=""; no_backup=false; automated=false
interactive=false
usage(){ echo "Usage: deploy.sh|update.sh [--artifact FILE] --host HOST [--user USER] [--port PORT] [--remote-dir DIR] [--config FILE]" >&2; exit 2; }
interactive=$([[ $# -eq 0 ]] && echo true || echo false)
while (($#)); do case "$1" in
  --artifact) artifact="${2:-}"; automated=true; shift 2;; --host) host="${2:-}"; shift 2;; --user) user="${2:-}"; shift 2;;
  --port) port="${2:-}"; shift 2;; --remote-dir) remote_dir="${2:-}"; shift 2;;
  --source-revision) source_revision="${2:-}"; shift 2;; --env) env_source="${2:-}"; automated=true; shift 2;;
  --install-root) install_root="${2:-}"; automated=true; shift 2;; --no-backup) no_backup=true; automated=true; shift;;
  --config) config_file="${2:-}"; shift 2;;
  -h|--help) usage;; *) usage;; esac; done
if [[ -f "$config_file" ]]; then
  # shellcheck disable=SC1090
  source "$config_file"
  host="${host:-${RBF_DEPLOY_HOST:-}}"; user="${user:-${RBF_DEPLOY_USER:-root}}"
  port="${port:-${RBF_DEPLOY_PORT:-22}}"; remote_dir="${remote_dir:-${RBF_DEPLOY_REMOTE_DIR:-/tmp/rbf-release}}"
  install_root="${install_root:-${RBF_DEPLOY_INSTALL_ROOT:-}}"; env_source="${env_source:-${RBF_DEPLOY_ENV_SOURCE:-}}"
fi
if [[ "$interactive" == true ]]; then
  [[ -t 0 && -t 1 ]] || { echo "[origin] Ohne Flags benötigt deploy ein interaktives Terminal." >&2; exit 2; }
  read -r -p "Webseitenserver [${host}]: " answer; host="${answer:-$host}"
  read -r -p "SSH-Benutzer [${user:-root}]: " answer; user="${answer:-${user:-root}}"
  read -r -p "SSH-Port [${port:-22}]: " answer; port="${answer:-${port:-22}}"
  read -r -p "Remote-Arbeitsverzeichnis [${remote_dir}]: " answer; remote_dir="${answer:-$remote_dir}"
  read -r -p "Vorhandenes Artefakt (leer = neu bauen): " artifact
  read -r -p "Quellrevision [HEAD]: " source_revision
fi
[[ -n "$host" ]] || usage; user="${user:-root}"
if [[ "$interactive" == true || ! -f "$config_file" ]]; then
  umask 077; temporary="${config_file}.tmp.$$"
  install -d -m 0700 "$(dirname "$config_file")"
  cat > "$temporary" <<EOF
RBF_DEPLOY_HOST=$(printf '%q' "$host")
RBF_DEPLOY_USER=$(printf '%q' "$user")
RBF_DEPLOY_PORT=$(printf '%q' "$port")
RBF_DEPLOY_REMOTE_DIR=$(printf '%q' "$remote_dir")
RBF_DEPLOY_INSTALL_ROOT=$(printf '%q' "$install_root")
RBF_DEPLOY_ENV_SOURCE=$(printf '%q' "$env_source")
EOF
  mv -f "$temporary" "$config_file"
  chmod 0600 "$config_file"
fi
if [[ -z "$artifact" ]]; then
  args=(--output-dir "$ROOT_DIR/release"); [[ -z "$source_revision" ]] || args+=(--source-revision "$source_revision")
  "$SCRIPT_DIR/build-artifact.sh" "${args[@]}"
  artifact="$(find "$ROOT_DIR/release" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
fi
artifact="$(realpath "$artifact")"; checksum="$artifact.sha256"
[[ -f "$artifact" && -f "$checksum" ]] || { echo "[origin] Artefakt oder Prüfsumme fehlt." >&2; exit 1; }
ssh -p "$port" "$user@$host" "mkdir -p '$remote_dir'"
scp -P "$port" "$artifact" "$checksum" "$ROOT_DIR/infrastructure/scripts/release/setup_website.sh" "$ROOT_DIR/infrastructure/scripts/release/verify-artifact.py" "$user@$host:$remote_dir/"
remote_command=(sudo bash "$remote_dir/setup_website.sh")
if [[ "$automated" == true ]]; then
  remote_command+=(--artifact "$remote_dir/$(basename "$artifact")" --checksum "$remote_dir/$(basename "$checksum")")
  [[ -z "$install_root" ]] || remote_command+=(--install-root "$install_root")
  [[ -z "$env_source" ]] || remote_command+=(--env "$env_source")
  [[ "$no_backup" == true ]] && remote_command+=(--no-backup)
fi
remote_line=""; for word in "${remote_command[@]}"; do printf -v quoted ' %q' "$word"; remote_line+="$quoted"; done
ssh -t -p "$port" "$user@$host" "$remote_line"
