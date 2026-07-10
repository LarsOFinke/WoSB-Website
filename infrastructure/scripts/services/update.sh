#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"

if [[ -d "$REPO_ROOT/.git" ]]; then
  log "Repository wird per fast-forward aktualisiert."
  git -C "$REPO_ROOT" pull --ff-only
else
  warn "Kein .git-Verzeichnis gefunden; Quellcode-Update wird übersprungen."
fi

bw_compose build --pull api gateway
deploy_stack
"$INFRA_DIR/scripts/checks/smoke-test.sh"
