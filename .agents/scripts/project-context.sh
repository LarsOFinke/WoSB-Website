#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

version="$(<VERSION)"
branch="$(git branch --show-current 2>/dev/null || true)"
revision="$(git rev-parse --short HEAD 2>/dev/null || true)"
mapfile -t changes < <(git status --short)

printf 'project=Royal Blackwater Fleet\n'
printf 'version=%s\n' "$version"
printf 'revision=%s@%s\n' "${branch:-detached}" "${revision:-unknown}"
printf 'runtime=Browser -> NGINX -> Spring Boot -> PostgreSQL\n'
printf 'working_tree_changes=%d\n' "${#changes[@]}"
printf 'primary_rules=AGENTS.md,docs/development/QUALITY_STANDARDS.md\n'
printf 'deployment_docs=docs/deployment/DEPLOYMENT.md,docs/debugging/2026-08-04-update-path-review.md\n'
printf 'incident_index=docs/debugging/DEPLOYMENT_INCIDENTS.md\n'
printf 'full_gate=make validate\n'

if ((${#changes[@]})); then
  printf '\nchanged_files:\n'
  printf '%s\n' "${changes[@]}"
fi
