#!/usr/bin/env bash
set -Eeuo pipefail
umask 022

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(cd -- "$SCRIPT_DIR/../../recovery-tool" && pwd -P)"
PYTHON_COMMAND="${PYTHON_COMMAND:-python3}"
AGE_EXECUTABLE="${AGE_EXECUTABLE:-$(command -v age || true)}"
AGE_KEYGEN_EXECUTABLE="${AGE_KEYGEN_EXECUTABLE:-$(command -v age-keygen || true)}"
ARCH="$(uname -m)"
case "$ARCH" in x86_64|aarch64|arm64) ;; *) echo "Unsupported Linux architecture: $ARCH" >&2; exit 1 ;; esac

OUTPUT_NAME="RBF-Recovery-Tool-Linux-${ARCH}"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"
VENV="$SCRIPT_DIR/.venv-build"
[[ -x "$AGE_EXECUTABLE" && -x "$AGE_KEYGEN_EXECUTABLE" ]] || {
  echo "age and age-keygen are required; install the age package first." >&2; exit 1;
}
command -v "$PYTHON_COMMAND" >/dev/null || { echo "Python was not found: $PYTHON_COMMAND" >&2; exit 1; }
"$PYTHON_COMMAND" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'
command -v realpath >/dev/null || { echo "realpath is required." >&2; exit 1; }
if [[ -e "$VENV" ]] && ! "$VENV/bin/python" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
  rm -rf -- "$VENV"
fi
[[ -x "$VENV/bin/python" ]] || "$PYTHON_COMMAND" -m venv "$VENV"
PYTHON="$VENV/bin/python"
rm -rf -- "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$DIST_DIR"
"$PYTHON" -m pip install --disable-pip-version-check -r "$COMMON_DIR/requirements-build.lock"
export RBF_AGE_EXE="$(realpath "$AGE_EXECUTABLE")" RBF_AGE_KEYGEN_EXE="$(realpath "$AGE_KEYGEN_EXECUTABLE")"
export RBF_OUTPUT_NAME="$OUTPUT_NAME" RBF_CONSOLE=1 PYTHONDONTWRITEBYTECODE=1
"$PYTHON" -m PyInstaller --noconfirm --clean --distpath "$DIST_DIR" --workpath "$BUILD_DIR" "$COMMON_DIR/rbf-recovery-tool.spec"
OUTPUT="$DIST_DIR/$OUTPUT_NAME"
[[ -x "$OUTPUT" ]] || { echo "Build output is missing: $OUTPUT" >&2; exit 1; }
(cd "$DIST_DIR" && sha256sum "$OUTPUT_NAME" > "$OUTPUT_NAME.sha256")
printf 'Built %s\n' "$OUTPUT"

