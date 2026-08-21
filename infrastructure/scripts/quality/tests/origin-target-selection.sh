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

operator_home="$work/operator-home"
repository_root="$work/repository"
mkdir -p "$operator_home/.ssh" "$repository_root"
resolved_identity="$(HOME="$operator_home" rbf_origin_resolve_identity_path deploy-test)"
[[ "$resolved_identity" == "$operator_home/.ssh/deploy-test" ]] \
  || fail 'relative identity names are not rooted in the private SSH directory'
rbf_origin_require_external_identity "$repository_root" "$resolved_identity" \
  || fail 'external identity path was rejected'
if rbf_origin_require_external_identity "$repository_root" "$repository_root/deploy-key" >/dev/null 2>&1; then
  fail 'repository-local identity path was accepted'
fi
if rbf_origin_require_external_identity "$repository_root" deploy-key >/dev/null 2>&1; then
  fail 'unresolved relative identity path was accepted'
fi
default_identity="$(HOME="$operator_home" rbf_origin_default_identity_path production rbfadmin)"
[[ "$default_identity" == "$operator_home/.ssh/rbf-deploy-production-rbfadmin" ]] \
  || fail 'target-specific default identity path is wrong'
legacy_suggestion="$(HOME="$operator_home" rbf_origin_configure_identity_suggestion \
  "$repository_root" "$repository_root/legacy-key" test rbfadmin 2>/dev/null)"
[[ "$legacy_suggestion" == "$operator_home/.ssh/rbf-deploy-test-rbfadmin" ]] \
  || fail 'interactive reconfiguration did not migrate a repository-local identity path'
external_suggestion="$(HOME="$operator_home" rbf_origin_configure_identity_suggestion \
  "$repository_root" "$operator_home/.ssh/existing-key" test rbfadmin)"
[[ "$external_suggestion" == "$operator_home/.ssh/existing-key" ]] \
  || fail 'interactive reconfiguration did not preserve an external identity path'

bash "$ROOT_DIR/infrastructure/scripts/quality/tests/build-restore.sh"

grep -q -- '--test|--production' "$ROOT_DIR/infrastructure/scripts/release/deploy-from-origin.sh" \
  || fail 'deploy dispatcher does not consume target flags'
grep -q -- '--production' "$ROOT_DIR/infrastructure/scripts/diagnostics/collect-from-origin.sh" \
  || fail 'diagnostics do not expose production selection'
for consumer in \
  infrastructure/scripts/release/deploy-from-origin.sh \
  infrastructure/scripts/diagnostics/collect-from-origin.sh \
  infrastructure/scripts/migration/restore-builds-from-origin.sh; do
  grep -q 'rbf_origin_require_external_identity' "$ROOT_DIR/$consumer" \
    || fail "$consumer does not reject repository-local SSH identities"
done

printf '[origin-target-test] OK: test default, explicit production and config override\n'
