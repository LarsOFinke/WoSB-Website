#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ARCH="$(uname -m)"
SOURCE="${1:-$SCRIPT_DIR/dist/RBF-Recovery-Tool-Linux-${ARCH}}"
BIN_DIR="${HOME}/.local/bin"
APPLICATIONS_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
TARGET="$BIN_DIR/rbf-recovery-tool"
DESKTOP_FILE="$APPLICATIONS_DIR/rbf-recovery-tool.desktop"

[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || {
  echo "Das Recovery-Binary wurde nicht gefunden oder ist ein Symlink: $SOURCE" >&2
  exit 1
}

mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"
install -m 0700 "$SOURCE" "$TARGET"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=RBF Recovery Tool
Comment=Royal Blackwater Fleet Disaster-Recovery-Backups abrufen und prüfen
Exec=$TARGET
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
chmod 0644 "$DESKTOP_FILE"

printf 'Installiert: %s\nDesktop-Eintrag: %s\n' "$TARGET" "$DESKTOP_FILE"
printf 'Start über das Anwendungsmenü oder mit: %s\n' "$TARGET"
