#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
run=false
[[ "${1:-}" != "--run" ]] || run=true
[[ $# -le 1 && ( $# -eq 0 || "$1" == "--run" ) ]] || {
  echo 'Usage: .agents/scripts/check-changes.sh [--run]' >&2
  exit 2
}
cd "$ROOT_DIR"

mapfile -t changed_files < <(
  { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u
)

if ((${#changed_files[@]} == 0)); then
  echo '[agent-check] Keine geänderten Dateien.'
  exit 0
fi

frontend=false
backend=false
infrastructure=false
specification=false
documentation=false
crosscutting=false
for path in "${changed_files[@]}"; do
  case "$path" in
    frontend/*) frontend=true ;;
    spring-api/*) backend=true ;;
    infrastructure/*|deploy.sh|update.sh|.agents/scripts/*)
      infrastructure=true
      ;;
    openapi/*|spring-api/src/main/reference/*|infrastructure/scripts/generation/*) specification=true ;;
    docs/*|.agents/*.md|README.md|AGENTS.md|SECURITY.md|infrastructure/scripts/quality/check_documentation.py)
      documentation=true
      ;;
    Makefile|infrastructure/scripts/quality/validate.sh|infrastructure/scripts/quality/check_repository.py|.github/workflows/*)
      crosscutting=true
      ;;
  esac
done

scope_count=0
for active in "$frontend" "$backend" "$infrastructure" "$specification"; do
  [[ "$active" != true ]] || ((scope_count += 1))
done

commands=()
if [[ "$crosscutting" == true ]] || ((scope_count > 1)) || [[ "$specification" == true ]]; then
  commands+=("bash .agents/scripts/check-all.sh")
else
  [[ "$frontend" != true ]] || commands+=("bash .agents/scripts/check-frontend.sh")
  [[ "$backend" != true ]] || commands+=("bash .agents/scripts/check-backend.sh")
  if [[ "$infrastructure" == true ]]; then
    commands+=("bash .agents/scripts/check-infrastructure.sh")
  fi
  [[ "$frontend" == true || "$backend" == true || "$infrastructure" == true ]] \
    || commands+=("python3 infrastructure/scripts/quality/check_repository.py --strict-tree")
fi
[[ "$documentation" != true ]] || commands+=("bash .agents/scripts/check-docs.sh")

printf '[agent-check] Geänderte Dateien: %d\n' "${#changed_files[@]}"
printf '  %s\n' "${changed_files[@]}"
printf '[agent-check] Empfohlene Prüfungen:\n'
printf '  %s\n' "${commands[@]}"

[[ "$run" != true ]] || for command in "${commands[@]}"; do
  printf '[agent-check] Starte: %s\n' "$command"
  bash -lc "$command"
done
