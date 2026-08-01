#!/usr/bin/env bash
set -Eeuo pipefail
umask 022

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DIST_DIR="$SCRIPT_DIR/dist"
ARCH="$(uname -m)"
PACKAGE="RBF-Recovery-Tool-Linux-${ARCH}-installer"
ARCHIVE_NAME="${PACKAGE}.tar.gz"
ARCHIVE="$DIST_DIR/$ARCHIVE_NAME"

# As with the DEB builder, delete stale package output before validating the
# input binary so failure cannot be mistaken for a successful rebuild.
mkdir -p "$DIST_DIR"
rm -f -- "$ARCHIVE" "$ARCHIVE.sha256"

BINARY="${1:-$DIST_DIR/RBF-Recovery-Tool-Linux-${ARCH}}"
[[ -f "$BINARY" && -x "$BINARY" ]] || {
  echo "Binary fehlt oder ist nicht ausführbar: $BINARY" >&2
  exit 1
}

for command_name in gzip sha256sum tar; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Erforderliches Build-Werkzeug fehlt: $command_name" >&2
    exit 1
  }
done

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$PACKAGE/dist"
install -m 0700 "$BINARY" "$STAGE/$PACKAGE/dist/$(basename "$BINARY")"
for file in \
  Install-RbfRecoveryTool.sh \
  Provision-RbfRecoveryLab.sh \
  Setup-RbfRecoveryLab.sh; do
  install -m 0700 "$SCRIPT_DIR/$file" "$STAGE/$PACKAGE/$file"
done
install -m 0644 "$SCRIPT_DIR/README.md" "$STAGE/$PACKAGE/README.md"

SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-0}"
(
  cd "$STAGE"
  tar \
    --sort=name \
    --mtime="@$SOURCE_DATE_EPOCH" \
    --owner=0 \
    --group=0 \
    --numeric-owner \
    -cf - "$PACKAGE" | gzip -n -9 > "$ARCHIVE"
)
(
  cd "$DIST_DIR"
  sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
)

printf 'Installer-Paket: %s\n' "$ARCHIVE"
printf 'Prüfsumme: %s\n' "$ARCHIVE.sha256"
