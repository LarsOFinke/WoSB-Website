#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOT_DIR="$(cd "$INFRA_DIR/.." && pwd)"
VERSION="$(cat "$ROOT_DIR/VERSION")"
OUTPUT_DIR="${1:-$ROOT_DIR/release}"
COMPONENTS="${2:-api,secure-api,gateway}"

require() { command -v "$1" >/dev/null 2>&1 || { echo "Benötigtes Kommando fehlt: $1" >&2; exit 2; }; }
require docker
require python3

temporary_env=false
if [[ ! -f "$INFRA_DIR/.env" ]]; then
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  temporary_env=true
fi
cleanup() {
  [[ "$temporary_env" == true ]] || return 0
  rm -f "$INFRA_DIR/.env"
}
trap cleanup EXIT

echo "Baue Release-Images für $VERSION."
IFS=',' read -r -a COMPONENT_LIST <<< "$COMPONENTS"
compose_services=()
for component in "${COMPONENT_LIST[@]}"; do
  case "$component" in
    api|python) compose_services+=(api) ;;
    secure-api|java) compose_services+=(secure-api) ;;
    gateway|frontend) compose_services+=(gateway) ;;
    *) echo "Unbekannte Komponente: $component" >&2; exit 2 ;;
  esac
done
(
  cd "$INFRA_DIR"
  docker compose --env-file .env -f compose.yml build "${compose_services[@]}"
  for service in "${compose_services[@]}"; do
    docker tag "rbf-hub-$service:local" "rbf-hub-$service:$VERSION"
  done
)

python3 "$ROOT_DIR/scripts/package_deployment_artifact.py" \
  --version "$VERSION" \
  --git-commit "$(git -C "$ROOT_DIR" rev-parse HEAD 2>/dev/null || true)" \
  --components "$COMPONENTS" \
  --output-dir "$OUTPUT_DIR"
