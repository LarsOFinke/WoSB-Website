#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
output_dir="$ROOT_DIR/release"
source_revision=""

usage() {
  echo "Usage: build-artifact.sh [--output-dir DIR] [--source-revision REVISION]" >&2
  echo "       Without flags, an interactive dialog opens in the terminal." >&2
  exit 2
}

interactive_setup() {
  [[ -t 0 && -t 1 ]] || { echo "[release] Without flags, build-artifact.sh requires an interactive terminal." >&2; exit 2; }
  local answer
  read -r -p "Ausgabeverzeichnis [${output_dir}]: " answer
  [[ -z "$answer" ]] || output_dir="$answer"
  answer=""
  read -r -p "Quellrevision [HEAD]: " answer
  [[ -z "$answer" ]] || source_revision="$answer"
}

if (($# == 0)); then
  interactive_setup
fi

while (($#)); do
  case "$1" in
    --output-dir) output_dir="${2:-}"; shift 2 ;;
    --source-revision) source_revision="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

for command in java mvn node npm python3; do
  command -v "$command" >/dev/null 2>&1 || { echo "[release] Missing build tool: $command" >&2; exit 1; }
done
[[ -n "$source_revision" ]] || source_revision="$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || printf unknown)"
version="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
# Remove stale packaged JARs before validation so an older version can never be
# selected or accidentally carried into a release artifact.
find "$ROOT_DIR/spring-api/target" -maxdepth 1 -type f -name 'rbf-api-*.jar' ! -name '*.original' -delete 2>/dev/null || true

bash "$ROOT_DIR/infrastructure/scripts/quality/validate.sh" full
jar="$ROOT_DIR/spring-api/target/rbf-api-${version}.jar"
[[ -n "$jar" ]] || { echo "[release] Verified Spring Boot JAR is missing." >&2; exit 1; }
[[ -f "$jar" && ! -L "$jar" ]] || {
  echo "[release] Verified Spring Boot JAR for version $version is missing: $jar" >&2
  exit 1
}

python3 "$ROOT_DIR/infrastructure/scripts/release/package_deployment_artifact.py" \
  --version "$(cat "$ROOT_DIR/VERSION")" \
  --jar "$jar" \
  --frontend-dist "$ROOT_DIR/frontend/dist" \
  --output-dir "$output_dir" \
  --source-revision "$source_revision"
