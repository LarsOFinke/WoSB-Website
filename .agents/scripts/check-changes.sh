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
contracts=false
for path in "${changed_files[@]}"; do
  case "$path" in
    frontend/*) frontend=true ;;
    spring-api/*) backend=true ;;
    infrastructure/*|deploy.sh|update.sh|scripts/test-infrastructure.sh|scripts/test-update-management.sh)
      infrastructure=true
      ;;
    contracts/*|scripts/migration/*) contracts=true ;;
  esac
done

scope_count=0
for active in "$frontend" "$backend" "$infrastructure" "$contracts"; do
  [[ "$active" != true ]] || ((scope_count += 1))
done

commands=()
if ((scope_count > 1)) || [[ "$contracts" == true ]]; then
  commands+=("make validate")
else
  [[ "$frontend" != true ]] || commands+=("bash .agents/scripts/check-frontend.sh")
  [[ "$backend" != true ]] || commands+=("make spring-test")
  if [[ "$infrastructure" == true ]]; then
    commands+=("bash scripts/test-infrastructure.sh")
    commands+=("bash scripts/test-update-management.sh")
  fi
  commands+=("python3 scripts/check_repository.py --strict-tree")
fi

printf '[agent-check] Geänderte Dateien: %d\n' "${#changed_files[@]}"
printf '  %s\n' "${changed_files[@]}"
printf '[agent-check] Empfohlene Prüfungen:\n'
printf '  %s\n' "${commands[@]}"

[[ "$run" != true ]] || for command in "${commands[@]}"; do
  printf '[agent-check] Starte: %s\n' "$command"
  bash -lc "$command"
done
