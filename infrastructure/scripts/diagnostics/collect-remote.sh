#!/usr/bin/env bash
set -Eeuo pipefail

install_root=""; area=""; category="errors"; since="30m"; tail_lines="400"; match=""
usage() { echo 'Usage: collect-remote.sh --install-root DIR --area AREA [--category CATEGORY] [--since 30m] [--tail 400] [--match TEXT]'; }
while (($#)); do
  case "$1" in
    --install-root) install_root="${2:-}"; shift 2 ;; --area) area="${2:-}"; shift 2 ;;
    --category) category="${2:-}"; shift 2 ;; --since) since="${2:-}"; shift 2 ;;
    --tail) tail_lines="${2:-}"; shift 2 ;; --match) match="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;; *) usage >&2; exit 2 ;;
  esac
done
case "$area" in overview|staff|calendar|api|security|gateway|database|deployment|all) ;; *) echo '[diagnostic] invalid area' >&2; exit 2 ;; esac
case "$category" in errors|warnings|http-500|auth|migration|all) ;; *) echo '[diagnostic] invalid category' >&2; exit 2 ;; esac
[[ "$install_root" == /* && "$since" =~ ^[1-9][0-9]*(m|h|d)$ ]] || { echo '[diagnostic] invalid path or duration' >&2; exit 2; }
[[ "$tail_lines" =~ ^[0-9]+$ && "$tail_lines" -ge 1 && "$tail_lines" -le 2000 ]] || { echo '[diagnostic] invalid tail limit' >&2; exit 2; }
[[ "$match" != *$'\n'* && ${#match} -le 120 ]] || { echo '[diagnostic] invalid match text' >&2; exit 2; }

infra="$install_root/current/infrastructure"
[[ -d "$infra" && -f "$infra/scripts/lib/docker.sh" ]] || { echo "[diagnostic] active runtime missing below $install_root/current" >&2; exit 1; }
export RBF_RUNTIME_INFRA_DIR="$infra"
# The active release path is validated above.
# shellcheck disable=SC1090,SC1091
source "$infra/scripts/lib/docker.sh"

case "$category" in
  errors) category_pattern='error|exception|api_error|status=5[0-9][0-9]|failed|fatal|panic' ;;
  warnings) category_pattern='warn|error|exception|api_error|status=5[0-9][0-9]|failed|fatal|panic' ;;
  http-500) category_pattern='api_error status=500|status=500| 500 ' ;;
  auth) category_pattern='security_401|security_403|status=401|status=403| 401 | 403 ' ;;
  migration) category_pattern='flyway|migration|schema|checksum' ;;
  all) category_pattern='' ;;
esac
case "$area" in
  staff) area_pattern='/api/admin/|staff|registration.request|audit.log|security.dashboard' ;;
  calendar) area_pattern='/api/calendar/|calendar|raid.helper' ;;
  security) area_pattern='security_|/api/admin/logs|/api/admin/ip-blocks|csrf|authentication|authorization' ;;
  *) area_pattern='' ;;
esac

filter_stream() {
  awk -v area_pattern="$area_pattern" -v category_pattern="$category_pattern" -v needle="$match" '
    BEGIN { area_pattern=tolower(area_pattern); category_pattern=tolower(category_pattern); needle=tolower(needle) }
    {
      line=tolower($0)
      anchor=(area_pattern=="" || line ~ area_pattern) &&
             (category_pattern=="" || line ~ category_pattern) &&
             (needle=="" || index(line,needle)>0)
      if (anchor) { print; hits++; remaining=(category_pattern=="" ? 0 : 20); next }
      if (remaining>0) { print; remaining-- }
    }
    END { if (hits==0) print "[diagnostic] no matching log lines" }
  '
}

compose_logs() {
  printf '\n--- source=compose:%s ---\n' "$*"
  bw_compose logs --timestamps --no-color --since "$since" --tail "$tail_lines" "$@" 2>&1 | filter_stream
}
journal_since() {
  local amount="${since%?}" unit="${since: -1}"
  case "$unit" in m) echo "-$amount minutes" ;; h) echo "-$amount hours" ;; d) echo "-$amount days" ;; esac
}
journal_logs() {
  printf '\n--- source=journal:rbf-hub ---\n'
  journalctl --no-pager --output=short-iso --since "$(journal_since)" --lines "$tail_lines" \
    -u rbf-hub.service -u rbf-hub-backup.service -u rbf-hub-update.service 2>&1 | filter_stream
}

release_version="$(cat "$install_root/current/VERSION" 2>/dev/null || echo unknown)"
printf 'RBF_REMOTE_DIAGNOSTIC=1\nremote_collected_at=%s\nrelease_version=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$release_version"
if [[ "$area" == overview ]]; then
  printf '\n--- source=compose:status ---\n'; bw_compose ps
  printf '\n--- source=systemd:status ---\n'; systemctl --no-pager --full --lines=20 status rbf-hub.service 2>&1 || true
elif [[ "$area" == deployment ]]; then journal_logs
else
  case "$area" in
    staff|calendar) compose_logs api gateway ;;
    api) compose_logs api ;;
    security) compose_logs api gateway ;;
    gateway) compose_logs gateway ;;
    database) compose_logs postgres ;;
    all) compose_logs api gateway postgres; journal_logs ;;
  esac
fi
