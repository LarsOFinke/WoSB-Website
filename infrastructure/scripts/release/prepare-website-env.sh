#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
target_env="${1:?target environment path required}"
target_credentials="${2:?target credentials path required}"
target_environment="${3:-test}"; requested_hostname="${4:-}"; requested_ip="${5:-}"; requested_letsencrypt_email="${6:-}"
[[ "$target_environment" =~ ^(test|production)$ ]] || die "Invalid target environment: $target_environment"
source "$INFRA_DIR/scripts/lib/env.sh"
export ENV_FILE="$target_env"
install -d -m 0700 "$(dirname "$target_env")"
if [[ ! -f "$target_env" ]]; then
  if [[ "$target_environment" == production ]]; then
    [[ -n "$requested_hostname" && -n "$requested_letsencrypt_email" ]] \
      || die "Production setup needs a public hostname and LETSENCRYPT_EMAIL."
    initialize_env "$requested_hostname" "$requested_ip" false admin "RBF Command" letsencrypt "$requested_letsencrypt_email" false
    install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
    echo "[website] Production environment and first-run credentials were generated on the target."
  else
    initialize_env "" "" false admin "RBF Command" auto "" true
    install -m 0600 "$INFRA_DIR/first-run-credentials.txt" "$target_credentials"
    echo "[website] New environment file and first-run credentials were generated."
  fi
else
  chmod 0600 "$target_env"
fi
set_env_value DEPLOYMENT_ENVIRONMENT "$target_environment"
