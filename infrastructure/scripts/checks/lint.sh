#!/usr/bin/env bash
set -Eeuo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$INFRA_DIR/scripts/lib/common.sh"

require_command bash

log "Prüfe Bash-Syntax."
while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find "$INFRA_DIR" \
  -path "$INFRA_DIR/data" -prune -o \
  -path "$INFRA_DIR/.git" -prune -o \
  -type f -name '*.sh' -print0)

success "Statische Infrastruktur-Prüfungen erfolgreich."
