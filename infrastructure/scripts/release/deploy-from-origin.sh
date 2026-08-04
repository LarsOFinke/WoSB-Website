#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
config_file="${RBF_ORIGIN_CONFIG:-$ROOT_DIR/.env.origin}"
if [[ "$EUID" -eq 0 && -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
  echo "[origin] Hinweis: deploy.sh benötigt lokal kein sudo; führe den Transfer als $SUDO_USER aus." >&2
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
artifact=""; host=""; user=""; bootstrap_user=""; bootstrap_identity_file=""; port=""; remote_dir=""; identity_file=""; source_revision=""; env_source=""; install_root=""; no_backup=false; automated=false
interactive=false; configure=false
usage(){ echo "Usage: deploy.sh|update.sh [--configure] [--artifact FILE] [--host HOST] [--user USER] [--bootstrap-user USER] [--bootstrap-identity-file FILE] [--identity-file FILE] [--port PORT] [--remote-dir DIR] [--config FILE]" >&2; exit 2; }
discover_identity_file() {
  [[ -n "$identity_file" ]] && return 0
  [[ -n "${HOME:-}" && -n "$user" ]] || return 0
  local candidate="$HOME/.ssh/$user"
  [[ -f "$candidate" ]] && identity_file="$candidate"
}
configure_deploy_identity() {
  local answer suggested="${identity_file:-${HOME:-}/.ssh/$user}"
  read -r -p "SSH-Identity-Datei für $user [${suggested}]: " answer
  identity_file="${answer:-$suggested}"
  if [[ -n "$identity_file" && ! -f "$identity_file" ]]; then
    read -r -p "Deploy-Key fehlt. Jetzt als dedizierten Ed25519-Key ohne Passphrase erzeugen? [J/n]: " answer
    case "${answer,,}" in
      ""|j|ja|y|yes)
        command -v ssh-keygen >/dev/null 2>&1 || { echo "[origin] ssh-keygen fehlt auf dem Ursprungsrechner." >&2; exit 1; }
        install -d -m 0700 "$(dirname "$identity_file")"
        ssh-keygen -q -t ed25519 -a 100 -N "" -C "rbf-deployment-$user@$host" -f "$identity_file"
        chmod 0600 "$identity_file"
        chmod 0644 "$identity_file.pub"
        echo "[origin] Dedizierter Deploy-Key wurde erzeugt: $identity_file"
        ;;
      *) identity_file="" ;;
    esac
  fi
}
configure_bootstrap_access() {
  local answer suggested=""
  read -r -p "Initialer SSH-Benutzer für einen frischen Zielserver (leer = nicht benötigt): " answer
  bootstrap_user="$answer"
  [[ -n "$bootstrap_user" ]] || return 0
  [[ "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] \
    || { echo "[origin] Ungültiger Bootstrap-Benutzername: $bootstrap_user" >&2; exit 2; }
  if [[ -f "${HOME:-}/.ssh/$bootstrap_user" ]]; then suggested="${HOME:-}/.ssh/$bootstrap_user"; fi
  read -r -p "Identity für $bootstrap_user (leer = SSH-Konfiguration/Agent/Passwort) [${suggested}]: " answer
  bootstrap_identity_file="${answer:-$suggested}"
}
initial_argument_count=$#
while (($#)); do case "$1" in
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
if [[ -f "$config_file" ]]; then
  # shellcheck disable=SC1090
  source "$config_file"
  host="${host:-${RBF_DEPLOY_HOST:-}}"; user="${user:-${RBF_DEPLOY_USER:-rbfadmin}}"
  port="${port:-${RBF_DEPLOY_PORT:-22}}"; remote_dir="${remote_dir:-${RBF_DEPLOY_REMOTE_DIR:-/tmp/rbf-release}}"
  identity_file="${identity_file:-${RBF_DEPLOY_IDENTITY_FILE:-}}"
  install_root="${install_root:-${RBF_DEPLOY_INSTALL_ROOT:-}}"; env_source="${env_source:-${RBF_DEPLOY_ENV_SOURCE:-}}"
fi
port="${port:-22}"; remote_dir="${remote_dir:-/tmp/rbf-release}"
if [[ "$configure" == true || ( "$initial_argument_count" -eq 0 && ! -f "$config_file" ) ]]; then interactive=true; fi
if [[ "$interactive" == true ]]; then
  [[ -t 0 && -t 1 ]] || { echo "[origin] Ohne Flags benötigt deploy ein interaktives Terminal." >&2; exit 2; }
  read -r -p "Webseitenserver [${host}]: " answer; host="${answer:-$host}"
  read -r -p "SSH-Benutzer [${user:-rbfadmin}]: " answer; user="${answer:-${user:-rbfadmin}}"
  configure_deploy_identity
  configure_bootstrap_access
  read -r -p "SSH-Port [${port:-22}]: " answer; port="${answer:-${port:-22}}"
  read -r -p "Remote-Arbeitsverzeichnis [${remote_dir}]: " answer; remote_dir="${answer:-$remote_dir}"
  read -r -p "Vorhandenes Artefakt (leer = neu bauen): " artifact
  read -r -p "Quellrevision [HEAD]: " source_revision
fi
[[ -n "$host" ]] || usage; user="${user:-rbfadmin}"
discover_identity_file
[[ "$user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo "[origin] Ungültiger SSH-Benutzername: $user" >&2; exit 2; }
[[ -z "$bootstrap_user" || "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || { echo "[origin] Ungültiger Bootstrap-Benutzername: $bootstrap_user" >&2; exit 2; }
[[ -z "$bootstrap_identity_file" || -f "$bootstrap_identity_file" ]] || { echo "[origin] Bootstrap-Identity-Datei fehlt: $bootstrap_identity_file" >&2; exit 2; }
[[ "$port" =~ ^[0-9]+$ && "$port" -le 65535 ]] || { echo "[origin] Ungültiger SSH-Port: $port" >&2; exit 2; }
[[ "$remote_dir" == /* ]] || { echo "[origin] Remote-Arbeitsverzeichnis muss absolut sein: $remote_dir" >&2; exit 2; }
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
EOF
  mv -f "$temporary" "$config_file"
  chmod 0600 "$config_file"
fi
[[ "$EUID" -ne 0 ]] || echo "[origin] Hinweis: deploy.sh benötigt lokal kein sudo." >&2
[[ -z "$identity_file" || -f "$identity_file" ]] || { echo "[origin] SSH-Identity-Datei fehlt: $identity_file" >&2; exit 1; }
ssh_args=(-o BatchMode=yes -o IdentitiesOnly=yes -p "$port")
scp_args=(-o BatchMode=yes -o IdentitiesOnly=yes -P "$port")
if [[ -n "$identity_file" ]]; then
  ssh_args+=(-i "$identity_file")
  scp_args+=(-i "$identity_file")
fi
identity_label="${identity_file:-SSH-Agent}"
echo "[origin] Prüfe Schlüsselzugang: $user@$host:$port (Identity: $identity_label)."
bootstrap_deploy_access() (
  set -Eeuo pipefail
  [[ -n "$identity_file" ]] || { echo "[origin] Für den Bootstrap ist eine feste private Identity-Datei erforderlich." >&2; exit 1; }
  command -v ssh-keygen >/dev/null 2>&1 || { echo "[origin] ssh-keygen fehlt auf dem Ursprungsrechner." >&2; exit 1; }
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
  bootstrap_auth_label="${bootstrap_identity_file:-SSH-Konfiguration/Agent oder Passwort}"
  echo "[origin] Richte $user einmalig über $bootstrap_user@$host ein (Authentifizierung: $bootstrap_auth_label)."
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
  [[ "$generated_public_key" == false ]] || echo "[origin] Public Key wurde temporär aus der privaten Identity abgeleitet."
)

if ! ssh "${ssh_args[@]}" "$user@$host" "sudo -n /usr/bin/true"; then
  if [[ -z "$bootstrap_user" && -t 0 && -t 1 ]]; then
    read -r -p "Initialer SSH-Benutzer für die einmalige rbfadmin-Einrichtung: " bootstrap_user
    bootstrap_identity_default=""
    if [[ -f "${HOME:-}/.ssh/$bootstrap_user" ]]; then bootstrap_identity_default="${HOME:-}/.ssh/$bootstrap_user"; fi
    read -r -p "Identity für $bootstrap_user (leer = SSH-Konfiguration/Agent/Passwort) [${bootstrap_identity_default}]: " bootstrap_identity_file
    bootstrap_identity_file="${bootstrap_identity_file:-$bootstrap_identity_default}"
  fi
  [[ "$bootstrap_user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] \
    || { echo "[origin] Schlüsselzugang fehlt; --bootstrap-user USER ist erforderlich." >&2; exit 1; }
  [[ -z "$bootstrap_identity_file" || -f "$bootstrap_identity_file" ]] \
    || { echo "[origin] Bootstrap-Identity-Datei fehlt: $bootstrap_identity_file" >&2; exit 1; }
  bootstrap_deploy_access
  echo "[origin] Prüfe den neu eingerichteten Schlüsselzugang."
  ssh "${ssh_args[@]}" "$user@$host" "sudo -n /usr/bin/true" \
    || { echo "[origin] rbfadmin wurde provisioniert, der Key-only-Zugang ist jedoch weiterhin nicht einsatzbereit." >&2; exit 1; }
fi
if [[ -z "$artifact" ]]; then
  args=(--output-dir "$ROOT_DIR/release"); [[ -z "$source_revision" ]] || args+=(--source-revision "$source_revision")
  "$SCRIPT_DIR/build-artifact.sh" "${args[@]}"
  artifact="$(find "$ROOT_DIR/release" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
fi
artifact="$(realpath "$artifact")"; checksum="$artifact.sha256"
[[ -f "$artifact" && -f "$checksum" ]] || { echo "[origin] Artefakt oder Prüfsumme fehlt." >&2; exit 1; }
cleanup_remote_stage() {
  cleanup_command=(rm -f -- "$remote_dir/$(basename "$artifact")" "$remote_dir/$(basename "$checksum")" "$remote_dir/setup_website.sh" "$remote_dir/migrate-install-root.sh" "$remote_dir/cleanup-failed-release.sh" "$remote_dir/verify-artifact.py")
  cleanup_line=""; for word in "${cleanup_command[@]}"; do printf -v quoted ' %q' "$word"; cleanup_line+="$quoted"; done
  ssh "${ssh_args[@]}" "$user@$host" "$cleanup_line" \
    >/dev/null 2>&1 || echo "[origin] Remote-Staging konnte nicht bereinigt werden: $remote_dir" >&2
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
echo "[origin] Bereinige fehlgeschlagene, nicht aktive Releases auf dem Zielserver (falls vorhanden)."
ssh "${ssh_args[@]}" "$user@$host" "$cleanup_line"
remote_command=(sudo -n bash "$remote_dir/setup_website.sh")
remote_command+=(--artifact "$remote_dir/$(basename "$artifact")" --checksum "$remote_dir/$(basename "$checksum")")
if [[ "$automated" == true ]]; then
  [[ -z "$install_root" ]] || remote_command+=(--install-root "$install_root")
  [[ -z "$env_source" ]] || remote_command+=(--env "$env_source")
  [[ "$no_backup" == true ]] && remote_command+=(--no-backup)
fi
remote_line=""; for word in "${remote_command[@]}"; do printf -v quoted ' %q' "$word"; remote_line+="$quoted"; done
ssh "${ssh_args[@]}" "$user@$host" "$remote_line"
