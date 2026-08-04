#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
artifact=""; checksum=""; install_root="${RBF_INSTALL_ROOT:-/srv/rbf}"; env_source=""; no_backup=false; skip_backup=false; skip_host=false
usage() { echo "Usage: setup_website.sh [--artifact FILE --checksum FILE --install-root DIR --env FILE --no-backup --skip-host]" >&2; exit 2; }
if (($# == 0)); then
  [[ -t 0 && -t 1 ]] || { echo "[website] Ohne Flags benötigt setup_website.sh ein interaktives Terminal." >&2; exit 2; }
  cat <<'BANNER'

Royal Blackwater Fleet – Website-Server einrichten
===================================================
Dieser Assistent installiert ein geprüftes Release-Artefakt atomar.
Halte das vom Ursprungsserver übertragene .tar.gz und die .sha256-Datei bereit.
Eine bestehende Installation wird vor dem Update automatisch gesichert.

BANNER
  default_artifact="$(find "$SCRIPT_DIR" -maxdepth 1 -type f -name 'rbf-deployment-*.tar.gz' -print -quit 2>/dev/null || true)"
  read -r -p "1/5 Release-Artefakt [${default_artifact:-Pfad eingeben}]: " answer
  artifact="${answer:-$default_artifact}"
  read -r -p "2/5 Prüfsumme [${artifact}.sha256]: " checksum_answer
  checksum="${checksum_answer:-$artifact.sha256}"
  read -r -p "3/5 Installationsroot [${install_root}]: " root_answer
  [[ -z "$root_answer" ]] || install_root="$root_answer"
  read -r -p "4/5 Private Environment-Datei [automatisch erzeugen]: " env_source
  if [[ -L "$install_root/current" ]]; then
    echo "5/5 Bestehende Installation erkannt; ein koordiniertes Backup wird automatisch erstellt."
  else
    read -r -p "5/5 Erstinstallation ohne vorhandenes Backup? [J/n]: " backup_answer
    [[ -z "$backup_answer" || "${backup_answer,,}" =~ ^(j|ja|y|yes)$ ]] && no_backup=true
  fi
fi
while (($#)); do
  case "$1" in
    --artifact) artifact="${2:-}"; shift 2;;
    --checksum) checksum="${2:-}"; shift 2;;
    --install-root) install_root="${2:-}"; shift 2;;
    --env) env_source="${2:-}"; shift 2;;
    --no-backup) no_backup=true; shift;;
    --skip-backup) skip_backup=true; shift;;
    --skip-host) skip_host=true; shift;;
    -h|--help) usage;; *) usage;;
  esac
done
[[ -n "$artifact" ]] || usage
artifact="$(realpath "$artifact")"; checksum="$(realpath "${checksum:-$artifact.sha256}")"
[[ -f "$artifact" && -f "$checksum" ]] || { echo "[website] Artefakt oder Prüfsumme fehlt." >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || {
  sudo_args=(--artifact "$artifact" --checksum "$checksum" --install-root "$install_root")
  [[ -z "$env_source" ]] || sudo_args+=(--env "$env_source")
  [[ "$no_backup" == true ]] && sudo_args+=(--no-backup)
  [[ "$skip_backup" == true ]] && sudo_args+=(--skip-backup)
  [[ "$skip_host" == true ]] && sudo_args+=(--skip-host)
  exec sudo --preserve-env=RBF_INSTALL_ROOT bash "$0" "${sudo_args[@]}"
}
for command in flock python3 sha256sum systemctl; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "[website] Zielhost ist nicht vorbereitet: '$command' fehlt." >&2
    echo "[website] Dies muss auf dem Webseitenserver (nicht auf dem Backup-Server) zuerst eingerichtet werden." >&2
    exit 1
  }
done
verifier="$SCRIPT_DIR/verify-artifact.py"
[[ -f "$verifier" ]] || { echo "[website] verify-artifact.py fehlt neben setup_website.sh." >&2; exit 1; }
stage="$(mktemp -d /tmp/rbf-website-setup.XXXXXX)"; trap 'rm -rf "$stage"' EXIT
python3 "$verifier" "$artifact" "$stage/bundle" >/dev/null
installer="$stage/bundle/payload/infrastructure/scripts/release/install-artifact.sh"
[[ -x "$installer" ]] || { echo "[website] Release enthält keinen Installer." >&2; exit 1; }
host_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-host.sh"
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  [[ "$skip_host" == false ]] || { echo "[website] Docker/Compose fehlt; --skip-host verhindert die automatische Host-Vorbereitung." >&2; exit 1; }
  [[ -x "$host_prepare" ]] || { echo "[website] Release enthält keinen Host-Bootstrap." >&2; exit 1; }
  echo "[website] Docker/Compose fehlt. Installiere jetzt die erforderlichen Host-Abhängigkeiten."
  "$host_prepare"
fi
command -v docker >/dev/null 2>&1 || { echo "[website] Docker konnte nicht installiert werden." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[website] Docker Compose v2 fehlt oder ist nicht erreichbar." >&2; exit 1; }
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
    echo "[website] Alte und neue Installationsroot existieren gleichzeitig: $legacy_install_root und $install_root" >&2
    echo "[website] Automatische Migration wird aus Sicherheitsgründen abgebrochen." >&2
    exit 1
  fi
  [[ -x "$migration_helper" ]] || { echo "[website] Release enthält keinen Installationsroot-Migrationshelfer." >&2; exit 1; }
  echo "[website] Migriere die bestehende Installation automatisch von $legacy_install_root nach $install_root."
  "$migration_helper" "$legacy_install_root" "$install_root"
  target_had_current=true
fi
if [[ "$target_had_current" == false && "$no_backup" == false ]]; then
  shopt -s nullglob
  existing_releases=("$install_root/releases"/*)
  shopt -u nullglob
  if ((${#existing_releases[@]} > 0)); then
    echo "[website] Keine aktive Installation, aber vorhandene Releases unter $install_root/releases." >&2
    echo "[website] Automatische Erstinstallation wird aus Sicherheitsgründen abgebrochen." >&2
    exit 1
  fi
  no_backup=true
  echo "[website] Keine bestehende Installation gefunden; Erstinstallation wird ohne Pre-Deployment-Backup fortgesetzt."
fi
if [[ -z "$env_source" ]]; then
  env_source="$install_root/shared/.env"
  env_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-env.sh"
  [[ -x "$env_prepare" ]] || { echo "[website] Release enthält keinen Environment-Bootstrap." >&2; exit 1; }
  "$env_prepare" "$env_source" "$install_root/shared/first-run-credentials.txt"
fi
[[ -f "$env_source" ]] || { echo "[website] Environment-Datei fehlt: $env_source" >&2; exit 1; }
tls_prepare="$stage/bundle/payload/infrastructure/scripts/release/prepare-website-tls.sh"
[[ -x "$tls_prepare" ]] || { echo "[website] Release enthält keinen TLS-Bootstrap." >&2; exit 1; }
"$tls_prepare" "$env_source" "$install_root/shared"
printf '\n[website] Verifiziert. Installation wird vorbereitet:\n  Artefakt: %s\n  Ziel:     %s\n\n' "$artifact" "$install_root"
installer_args=(--artifact "$artifact" --checksum "$checksum" --install-root "$install_root" --requested-by origin)
[[ "$no_backup" == true ]] && installer_args+=(--no-backup)
[[ "$skip_backup" == true ]] && installer_args+=(--skip-backup)
[[ -z "$env_source" ]] || installer_args+=(--env "$env_source")
RBF_ARTIFACT_VERIFIER="$stage/bundle/payload/infrastructure/scripts/release/verify-artifact.py" \
  "$installer" "${installer_args[@]}"

credentials_file="$install_root/shared/first-run-credentials.txt"
if [[ -f "$credentials_file" && ! -L "$credentials_file" ]]; then
  printf '\n[website] First-Run-Zugangsdaten (einmalig sicher speichern):\n'
  sed -n '1,20p' "$credentials_file"
  printf '[website] Danach die Zugangsdaten-Datei sicher löschen: %s\n\n' "$credentials_file"
fi
