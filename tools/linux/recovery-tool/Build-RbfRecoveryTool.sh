#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(cd -- "$SCRIPT_DIR/../../recovery-tool" && pwd -P)"
PYTHON_COMMAND="${PYTHON_COMMAND:-python3}"
AGE_EXECUTABLE="${AGE_EXECUTABLE:-$(command -v age || true)}"
AGE_KEYGEN_EXECUTABLE="${AGE_KEYGEN_EXECUTABLE:-$(command -v age-keygen || true)}"
ARCH="$(uname -m)"
OUTPUT_NAME="RBF-Recovery-Tool-Linux-${ARCH}"
VENV="$SCRIPT_DIR/.venv-build"

[[ -n "$AGE_EXECUTABLE" && -x "$AGE_EXECUTABLE" ]] || {
  echo "age wurde nicht gefunden. Installiere es auf dem Linux-Buildsystem." >&2
  exit 1
}
[[ -n "$AGE_KEYGEN_EXECUTABLE" && -x "$AGE_KEYGEN_EXECUTABLE" ]] || {
  echo "age-keygen wurde nicht gefunden. Installiere es auf dem Linux-Buildsystem." >&2
  exit 1
}
command -v "$PYTHON_COMMAND" >/dev/null 2>&1 || {
  echo "Python wurde nicht gefunden: $PYTHON_COMMAND" >&2
  exit 1
}
"$PYTHON_COMMAND" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 oder neuer ist für den Build erforderlich.")
try:
    import tkinter
except ImportError as exc:
    raise SystemExit("Tkinter fehlt. Unter Debian/Ubuntu: sudo apt install python3-tk") from exc
PY

if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON_COMMAND" -m venv "$VENV"
fi
PYTHON="$VENV/bin/python"
"$PYTHON" -m pip install --disable-pip-version-check --upgrade pip
"$PYTHON" -m pip install --disable-pip-version-check -r "$COMMON_DIR/requirements-build.lock"

export RBF_AGE_EXE="$(realpath "$AGE_EXECUTABLE")"
export RBF_AGE_KEYGEN_EXE="$(realpath "$AGE_KEYGEN_EXECUTABLE")"
export RBF_OUTPUT_NAME="$OUTPUT_NAME"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$SCRIPT_DIR/dist" \
  --workpath "$SCRIPT_DIR/build" \
  "$COMMON_DIR/rbf-recovery-tool.spec"

OUTPUT="$SCRIPT_DIR/dist/$OUTPUT_NAME"
[[ -x "$OUTPUT" ]] || {
  echo "Build-Ausgabe fehlt oder ist nicht ausführbar: $OUTPUT" >&2
  exit 1
}
HASH="$(sha256sum "$OUTPUT" | awk '{print $1}')"
printf '\nFertig: %s\nSHA-256: %s\n' "$OUTPUT" "$HASH"
printf 'Auf dem Ziel-Laptop werden nur dieses Binary und die private age-Identität benötigt.\n'
