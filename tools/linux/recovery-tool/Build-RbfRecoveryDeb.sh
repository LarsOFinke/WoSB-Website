#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(cd -- "$SCRIPT_DIR/../../recovery-tool" && pwd -P)"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64) DEB_ARCH=amd64 ;;
  aarch64|arm64) DEB_ARCH=arm64 ;;
  *) echo "Nicht unterstützte Debian-Architektur: $ARCH_RAW" >&2; exit 1 ;;
esac
BINARY="${1:-$SCRIPT_DIR/dist/RBF-Recovery-Tool-Linux-${ARCH_RAW}}"
[[ -x "$BINARY" ]] || { echo "Binary fehlt: $BINARY" >&2; exit 1; }
VERSION="$(PYTHONPATH="$COMMON_DIR/src" python3 -c 'from rbf_recovery_tool import __version__; print(__version__)')"
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
install -m 0644 "$SCRIPT_DIR/README.md" \
  "$ROOT/usr/share/doc/rbf-recovery-tool/README.md"
cat > "$ROOT/usr/share/applications/rbf-recovery-tool.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=RBF Recovery Tool
Comment=Verschlüsselte RBF-Recovery-Backups abrufen, prüfen und lokal testen
Exec=/usr/bin/rbf-recovery-tool
Terminal=false
Categories=Utility;System;
StartupNotify=true
EOF
cat > "$ROOT/DEBIAN/control" <<EOF
Package: rbf-recovery-tool
Version: $VERSION
Section: admin
Priority: optional
Architecture: $DEB_ARCH
Maintainer: Royal Blackwater Fleet
Depends: libc6, libgcc-s1, libstdc++6, libx11-6, libxext6, libxrender1, libxft2, libfontconfig1, libfreetype6, policykit-1
Description: Encrypted Royal Blackwater Fleet disaster-recovery client
 Downloads and verifies age-encrypted recovery bundles over pinned-host-key SFTP.
 Includes an optional rootless-Docker PostgreSQL restore lab for Ubuntu.
EOF
OUTPUT="$SCRIPT_DIR/dist/rbf-recovery-tool_${VERSION}_${DEB_ARCH}.deb"
dpkg-deb --root-owner-group --build "$ROOT" "$OUTPUT" >/dev/null
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
printf 'Debian-Paket: %s\n' "$OUTPUT"
