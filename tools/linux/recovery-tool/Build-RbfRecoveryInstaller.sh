#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ARCH="$(uname -m)"
BINARY="${1:-$SCRIPT_DIR/dist/RBF-Recovery-Tool-Linux-${ARCH}}"
[[ -x "$BINARY" ]] || { echo "Binary fehlt: $BINARY" >&2; exit 1; }
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
PACKAGE="RBF-Recovery-Tool-Linux-${ARCH}-installer"
mkdir -p "$STAGE/$PACKAGE/dist"
install -m 0700 "$BINARY" "$STAGE/$PACKAGE/dist/$(basename "$BINARY")"
for file in \
  Install-RbfRecoveryTool.sh \
  Provision-RbfRecoveryLab.sh \
  Setup-RbfRecoveryLab.sh \
  README.md; do
  install -m 0700 "$SCRIPT_DIR/$file" "$STAGE/$PACKAGE/$file"
done
chmod 0644 "$STAGE/$PACKAGE/README.md"
(
  cd "$STAGE"
  tar -czf "$SCRIPT_DIR/dist/${PACKAGE}.tar.gz" "$PACKAGE"
)
sha256sum "$SCRIPT_DIR/dist/${PACKAGE}.tar.gz" \
  > "$SCRIPT_DIR/dist/${PACKAGE}.tar.gz.sha256"
printf 'Installer-Paket: %s\n' "$SCRIPT_DIR/dist/${PACKAGE}.tar.gz"
