#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MODE="${1:-full}"
[[ "$MODE" == quick || "$MODE" == full ]] || { echo 'Usage: infrastructure/scripts/quality/validate.sh [quick|full]' >&2; exit 2; }
created_frontend_env=false
cleanup(){ [[ "$created_frontend_env" == false ]] || rm -f "$ROOT_DIR/frontend/.env"; }
trap cleanup EXIT

python3 "$ROOT_DIR/infrastructure/scripts/quality/check_repository.py"
python3 "$ROOT_DIR/infrastructure/scripts/quality/check_documentation.py"
python3 "$ROOT_DIR/infrastructure/scripts/quality/security_audit.py"
python3 "$ROOT_DIR/infrastructure/scripts/quality/audit_spring_backend.py"
python3 "$ROOT_DIR/infrastructure/scripts/quality/audit_css.py"
if command -v javac >/dev/null 2>&1; then
  java_check_dir="$(mktemp -d)"
  javac -d "$java_check_dir" "$ROOT_DIR/infrastructure/scripts/quality/java/JavaSyntaxCheck.java"
  java -cp "$java_check_dir" JavaSyntaxCheck "$ROOT_DIR/spring-api/src"
  rm -rf "$java_check_dir"
elif [[ "$MODE" == full ]]; then
  echo '[test] A Java 21 JDK is required for full validation.' >&2; exit 1
fi
bash "$ROOT_DIR/infrastructure/scripts/quality/tests/infrastructure.sh"
bash "$ROOT_DIR/infrastructure/scripts/quality/tests/update-management.sh"
python3 -c 'import pytest' 2>/dev/null || {
  echo '[test] pytest is required; install CI test dependencies with: python3 -m pip install -r requirements-ci.txt' >&2
  exit 1
}
python3 -m pytest -q -p no:cacheprovider "$ROOT_DIR/tests/recovery" "$ROOT_DIR/tests/quality"

if command -v mvn >/dev/null 2>&1; then
  maven_repo_args=()
  [[ -z "${MAVEN_REPO_LOCAL:-}" ]] || maven_repo_args+=("-Dmaven.repo.local=$MAVEN_REPO_LOCAL")
  mvn "${maven_repo_args[@]}" -f "$ROOT_DIR/spring-api/pom.xml" --batch-mode --no-transfer-progress verify
elif [[ "$MODE" == full ]]; then
  echo '[test] Maven 3.9 is required for full validation.' >&2; exit 1
else
  echo '[test] Maven unavailable; Spring compilation skipped in quick mode.' >&2
fi

if command -v npm >/dev/null 2>&1; then
  if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    if [[ "$MODE" == full ]]; then
      (cd "$ROOT_DIR/frontend" && npm ci)
    else
      echo '[test] frontend dependencies absent; running dependency-free frontend tests.' >&2
      (cd "$ROOT_DIR/frontend" && npm run locales:generate && node --test tests/*.test.mjs)
    fi
  fi
  if [[ -d "$ROOT_DIR/frontend/node_modules" ]]; then
    if [[ ! -f "$ROOT_DIR/frontend/.env" ]]; then cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"; created_frontend_env=true; fi
    (cd "$ROOT_DIR/frontend" && npm run test:ci)
  fi
elif [[ "$MODE" == full ]]; then
  echo '[test] Node/npm are required for full validation.' >&2; exit 1
fi
rm -rf "$ROOT_DIR/frontend/src/locales/generated"
find "$ROOT_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$ROOT_DIR" -type f -name '*.pyc' -delete

python3 "$ROOT_DIR/infrastructure/scripts/quality/check_repository.py" --strict-tree
printf '[test] validation completed successfully\n'
