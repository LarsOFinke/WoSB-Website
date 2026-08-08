#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
# shellcheck source=../../lib/origin-target.sh
source "$ROOT_DIR/infrastructure/scripts/lib/origin-target.sh"

fail(){ printf '[origin-target-test] %s\n' "$*" >&2; exit 1; }
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT

unset RBF_ORIGIN_CONFIG || true
rbf_origin_select_target "$work"
[[ "$RBF_ORIGIN_TARGET" == test ]] || fail 'default target is not test'
[[ "$RBF_ORIGIN_CONFIG_FILE" == "$work/.env.origin.test" ]] || fail 'default test config path is wrong'

rbf_origin_select_target "$work" --test
[[ "$RBF_ORIGIN_TARGET" == test ]] || fail '--test did not select test'
[[ "$RBF_ORIGIN_CONFIG_FILE" == "$work/.env.origin.test" ]] || fail '--test config path is wrong'

rbf_origin_select_target "$work" --production
[[ "$RBF_ORIGIN_TARGET" == production ]] || fail '--production did not select production'
[[ "$RBF_ORIGIN_CONFIG_FILE" == "$work/.env.origin.production" ]] || fail 'production config path is wrong'

rbf_origin_select_target "$work" --production --config "$work/custom.env"
[[ "$RBF_ORIGIN_TARGET" == production ]] || fail 'custom config changed target label'
[[ "$RBF_ORIGIN_CONFIG_FILE" == "$work/custom.env" ]] || fail '--config did not override selected profile path'

RBF_ORIGIN_CONFIG="$work/from-environment.env" rbf_origin_select_target "$work" --production
[[ "$RBF_ORIGIN_CONFIG_FILE" == "$work/from-environment.env" ]] || fail 'RBF_ORIGIN_CONFIG did not override selected profile path'

if (rbf_origin_select_target "$work" --test --production >/dev/null 2>&1); then
  fail 'conflicting target flags were accepted'
fi
if (rbf_origin_select_target "$work" --config >/dev/null 2>&1); then
  fail 'missing --config value was accepted'
fi

grep -q -- '--test|--production' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" \
  || fail 'deploy dispatcher does not consume target flags'
grep -q -- '--production' "$ROOT_DIR/infrastructure/scripts/diagnostics/collect-from-origin.sh" \
  || fail 'diagnostics do not expose production selection'

printf '[origin-target-test] OK: test default, explicit production and config override\n'
