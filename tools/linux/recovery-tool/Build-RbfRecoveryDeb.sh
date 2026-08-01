#!/usr/bin/env bash
set -Eeuo pipefail
umask 022

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(cd -- "$SCRIPT_DIR/../../recovery-tool" && pwd -P)"
DIST_DIR="$SCRIPT_DIR/dist"

for command_name in dpkg-deb python3 sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Erforderliches Build-Werkzeug fehlt: $command_name" >&2
    exit 1
  }
done

ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64) DEB_ARCH=amd64 ;;
  aarch64|arm64) DEB_ARCH=arm64 ;;
  *) echo "Nicht unterstützte Debian-Architektur: $ARCH_RAW" >&2; exit 1 ;;
esac

# Remove stale packages before validating the new input binary. A failed
# standalone packaging attempt must not leave an installable-looking old DEB.
mkdir -p "$DIST_DIR"
find "$DIST_DIR" -maxdepth 1 -type f \
  \( -name "rbf-recovery-tool_*_${DEB_ARCH}.deb" \
     -o -name "rbf-recovery-tool_*_${DEB_ARCH}.deb.sha256" \) \
  -delete

BINARY="${1:-$DIST_DIR/RBF-Recovery-Tool-Linux-${ARCH_RAW}}"
[[ -f "$BINARY" && -x "$BINARY" ]] || {
  echo "Binary fehlt oder ist nicht ausführbar: $BINARY" >&2
  exit 1
}

VERSION="$(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$COMMON_DIR/src" python3 -c \
  'from rbf_recovery_tool import __version__; print(__version__)')"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([+~.-][0-9A-Za-z.+~:-]+)?$ ]] || {
  echo "Ungültige Debian-Paketversion: $VERSION" >&2
  exit 1
}

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
ROOT="$STAGE/rbf-recovery-tool_${VERSION}_${DEB_ARCH}"
mkdir -p \
  "$ROOT/DEBIAN" \
  "$ROOT/usr/bin" \
  "$ROOT/usr/lib/rbf-recovery-tool" \
  "$ROOT/usr/share/applications" \
  "$ROOT/usr/share/doc/rbf-recovery-tool"

install -m 0755 "$BINARY" "$ROOT/usr/bin/rbf-recovery-tool"
install -m 0755 "$SCRIPT_DIR/Provision-RbfRecoveryLab.sh" \
  "$ROOT/usr/lib/rbf-recovery-tool/Provision-RbfRecoveryLab.sh"
install -m 0755 "$SCRIPT_DIR/Setup-RbfRecoveryLab.sh" \
  "$ROOT/usr/lib/rbf-recovery-tool/Setup-RbfRecoveryLab.sh"
install -m 0755 "$SCRIPT_DIR/Provision-RbfBackupServer.sh" \
  "$ROOT/usr/lib/rbf-recovery-tool/Provision-RbfBackupServer.sh"
install -m 0644 "$SCRIPT_DIR/README.md" \
  "$ROOT/usr/share/doc/rbf-recovery-tool/README.md"

cat > "$ROOT/usr/share/applications/rbf-recovery-tool.desktop" <<'EOF_DESKTOP'
[Desktop Entry]
Type=Application
Name=RBF Recovery Tool
Comment=Verschlüsselte RBF-Recovery-Backups abrufen, prüfen und lokal testen
Exec=/usr/bin/rbf-recovery-tool
TryExec=/usr/bin/rbf-recovery-tool
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF_DESKTOP

cat > "$ROOT/DEBIAN/control" <<EOF_CONTROL
Package: rbf-recovery-tool
Version: $VERSION
Section: admin
Priority: optional
Architecture: $DEB_ARCH
Maintainer: Royal Blackwater Fleet
Depends: libc6, libgcc-s1, libstdc++6, libx11-6, libxext6, libxrender1, libxft2, libfontconfig1, libfreetype6, openssh-client, pkexec
Description: Encrypted Royal Blackwater Fleet disaster-recovery client
 Downloads and verifies age-encrypted recovery bundles over pinned-host-key SFTP.
 Includes an optional rootless-Docker PostgreSQL restore lab and a hardened
 assisted SFTP backup-server provisioner for Ubuntu.
EOF_CONTROL

OUTPUT_NAME="rbf-recovery-tool_${VERSION}_${DEB_ARCH}.deb"
OUTPUT="$DIST_DIR/$OUTPUT_NAME"
rm -f "$OUTPUT" "$OUTPUT.sha256"
dpkg-deb --root-owner-group --build "$ROOT" "$OUTPUT" >/dev/null

# Guard against regressions in the generated package metadata.
PACKAGE_DEPENDS="$(dpkg-deb -f "$OUTPUT" Depends)"
[[ ",$PACKAGE_DEPENDS," == *", pkexec,"* || ",$PACKAGE_DEPENDS," == *",pkexec,"* ]] || {
  echo "Paketprüfung fehlgeschlagen: pkexec fehlt in Depends: $PACKAGE_DEPENDS" >&2
  exit 1
}
[[ ",$PACKAGE_DEPENDS," == *", openssh-client,"* || ",$PACKAGE_DEPENDS," == *",openssh-client,"* ]] || {
  echo "Paketprüfung fehlgeschlagen: openssh-client fehlt in Depends: $PACKAGE_DEPENDS" >&2
  exit 1
}
[[ "$PACKAGE_DEPENDS" != *"policykit-1"* ]] || {
  echo "Paketprüfung fehlgeschlagen: veraltete Abhängigkeit policykit-1 enthalten." >&2
  exit 1
}

(
  cd "$DIST_DIR"
  sha256sum "$OUTPUT_NAME" > "$OUTPUT_NAME.sha256"
)

printf 'Debian-Paket: %s\n' "$OUTPUT"
printf 'Abhängigkeiten: %s\n' "$PACKAGE_DEPENDS"
printf 'Prüfsumme: %s\n' "$OUTPUT.sha256"
