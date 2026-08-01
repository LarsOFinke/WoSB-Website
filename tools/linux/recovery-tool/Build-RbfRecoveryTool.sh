#!/usr/bin/env bash
set -Eeuo pipefail
umask 022

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(cd -- "$SCRIPT_DIR/../../recovery-tool" && pwd -P)"
PYTHON_COMMAND="${PYTHON_COMMAND:-python3}"
AGE_EXECUTABLE="${AGE_EXECUTABLE:-$(command -v age || true)}"
AGE_KEYGEN_EXECUTABLE="${AGE_KEYGEN_EXECUTABLE:-$(command -v age-keygen || true)}"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|aarch64|arm64) ;;
  *) echo "Nicht unterstützte Linux-Architektur: $ARCH" >&2; exit 1 ;;
esac

OUTPUT_NAME="RBF-Recovery-Tool-Linux-${ARCH}"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"
VENV="$SCRIPT_DIR/.venv-build"

# dist/ and build/ contain generated output only. Remove them before checking
# prerequisites so a failed rebuild can never leave an older package looking
# like the result of the current invocation.
rm -rf -- "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$DIST_DIR"

[[ -n "$AGE_EXECUTABLE" && -x "$AGE_EXECUTABLE" ]] || {
  echo "age wurde nicht gefunden. Unter Debian/Ubuntu: sudo apt install age" >&2
  exit 1
}
[[ -n "$AGE_KEYGEN_EXECUTABLE" && -x "$AGE_KEYGEN_EXECUTABLE" ]] || {
  echo "age-keygen wurde nicht gefunden. Unter Debian/Ubuntu: sudo apt install age" >&2
  exit 1
}
command -v "$PYTHON_COMMAND" >/dev/null 2>&1 || {
  echo "Python wurde nicht gefunden: $PYTHON_COMMAND" >&2
  exit 1
}
for command_name in realpath sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Erforderliches Build-Werkzeug fehlt: $command_name" >&2
    exit 1
  }
done

"$PYTHON_COMMAND" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 oder neuer ist für den Build erforderlich.")
try:
    import tkinter
except ImportError as exc:
    raise SystemExit("Tkinter fehlt. Unter Debian/Ubuntu: sudo apt install python3-tk") from exc
PY

# Recreate stale or broken build environments instead of failing later with an
# opaque interpreter error after a Python upgrade.
if [[ -e "$VENV" ]] && ! "$VENV/bin/python" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
  echo "Veraltete oder defekte Build-Umgebung wird neu erstellt: $VENV"
  rm -rf "$VENV"
fi
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON_COMMAND" -m venv "$VENV"
fi
PYTHON="$VENV/bin/python"
"$PYTHON" -m pip install --disable-pip-version-check -r "$COMMON_DIR/requirements-build.lock"

export PYTHONDONTWRITEBYTECODE=1
export RBF_AGE_EXE="$(realpath "$AGE_EXECUTABLE")"
export RBF_AGE_KEYGEN_EXE="$(realpath "$AGE_KEYGEN_EXECUTABLE")"
export RBF_OUTPUT_NAME="$OUTPUT_NAME"
export RBF_CONSOLE=1
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$COMMON_DIR/rbf-recovery-tool.spec"

OUTPUT="$DIST_DIR/$OUTPUT_NAME"
[[ -f "$OUTPUT" && -x "$OUTPUT" ]] || {
  echo "Build-Ausgabe fehlt oder ist nicht ausführbar: $OUTPUT" >&2
  exit 1
}
"$OUTPUT" --help >/dev/null
(
  cd "$DIST_DIR"
  sha256sum "$OUTPUT_NAME" > "$OUTPUT_NAME.sha256"
)

"$SCRIPT_DIR/Build-RbfRecoveryInstaller.sh" "$OUTPUT"
"$SCRIPT_DIR/Build-RbfRecoveryDeb.sh" "$OUTPUT"

HASH="$(sha256sum "$OUTPUT" | awk '{print $1}')"
printf '\nFertig: %s\nSHA-256: %s\n' "$OUTPUT" "$HASH"
printf 'Alle erzeugten Dateien liegen unter %s und sind nicht für Git vorgesehen.\n' "$DIST_DIR"
