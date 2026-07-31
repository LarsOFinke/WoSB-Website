#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ARCH="$(uname -m)"
SOURCE="$SCRIPT_DIR/dist/RBF-Recovery-Tool-Linux-${ARCH}"
with_db_lab=false
with_timer=false
non_interactive=false
while (($#)); do
  case "$1" in
    --binary) SOURCE="${2:-}"; shift 2; continue ;;
    --with-db-lab) with_db_lab=true ;;
    --with-timer) with_timer=true ;;
    --non-interactive) non_interactive=true ;;
    *) echo "Unbekannte Option: $1" >&2; exit 2 ;;
  esac
  shift
done

BIN_DIR="${HOME}/.local/bin"
LIB_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/rbf-recovery-tool"
APPLICATIONS_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
TARGET="$BIN_DIR/rbf-recovery-tool"
DESKTOP_FILE="$APPLICATIONS_DIR/rbf-recovery-tool.desktop"

[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || {
  echo "Das Recovery-Binary wurde nicht gefunden oder ist ein Symlink: $SOURCE" >&2
  exit 1
}
mkdir -p "$BIN_DIR" "$LIB_DIR" "$APPLICATIONS_DIR"
install -m 0700 "$SOURCE" "$TARGET"
for helper in Provision-RbfRecoveryLab.sh Setup-RbfRecoveryLab.sh; do
  [[ -f "$SCRIPT_DIR/$helper" ]] || { echo "Hilfsskript fehlt: $helper" >&2; exit 1; }
  install -m 0700 "$SCRIPT_DIR/$helper" "$LIB_DIR/$helper"
done
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=RBF Recovery Tool
Comment=Verschlüsselte Royal-Blackwater-Fleet-Recovery-Backups abrufen, prüfen und testen
Exec=$TARGET
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
chmod 0644 "$DESKTOP_FILE"

if [[ "$non_interactive" == false ]]; then
  if [[ "$with_timer" == false ]]; then
    read -r -p "Täglichen automatischen Pull per systemd-Benutzertimer einrichten? [y/N] " answer
    [[ "$answer" =~ ^[YyJj]$ ]] && with_timer=true
  fi
  if [[ "$with_db_lab" == false ]]; then
    read -r -p "Optionales lokales PostgreSQL-Recovery-Labor mit rootless Docker einrichten? [y/N] " answer
    [[ "$answer" =~ ^[YyJj]$ ]] && with_db_lab=true
  fi
fi

if [[ "$with_timer" == true ]]; then
  if ! "$TARGET" timer install; then
    echo "Timer wurde nicht aktiviert. Zuerst Profil, SSH-Key und age-Identität in der GUI konfigurieren." >&2
  fi
fi

if [[ "$with_db_lab" == true ]]; then
  if docker --context rootless info --format '{{json .SecurityOptions}}' 2>/dev/null | grep -qi rootless; then
    "$LIB_DIR/Setup-RbfRecoveryLab.sh" "$TARGET"
  else
    echo "Rootless Docker ist noch nicht eingerichtet." >&2
    echo "Für die sichere Ein-Klick-Provisionierung installiere bevorzugt das erzeugte Debian-Paket." >&2
    echo "Alternativ das Provisionierungs-Hilfsskript bewusst einmalig administrativ ausführen und danach:" >&2
    echo "  $LIB_DIR/Setup-RbfRecoveryLab.sh $TARGET" >&2
  fi
fi

printf 'Installiert: %s\nDesktop-Eintrag: %s\n' "$TARGET" "$DESKTOP_FILE"
printf 'Start über das Anwendungsmenü oder mit: %s\n' "$TARGET"
