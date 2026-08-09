#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=../lib/origin-target.sh
source "$SCRIPT_DIR/../lib/origin-target.sh"

rbf_origin_select_target "$ROOT_DIR" "$@"
target_environment="$RBF_ORIGIN_TARGET"
config_file="$RBF_ORIGIN_CONFIG_FILE"
backup_file=""
dry_run_only=false
declare -a requested_owner_mappings=()
expected_builds=""; expected_slots=""; expected_classifications=""

usage() {
  cat <<'EOF'
Usage: infrastructure/scripts/migration/restore-builds-from-origin.sh [OPTIONS]

Restores a portable build-only SQL backup from backups/ through the configured
test server by default. A complete transactional dry run always runs first.

  --test                 Use the test server (default)
  --production           Use the production server (explicit opt-in)
  --config FILE          Override the selected origin connection profile
  --backup FILE          Select a build backup (auto-selected when unambiguous)
  --owner SOURCE=TARGET  Map a backup owner to an existing target username
                         (repeatable; otherwise prompted/defaulted)
  --dry-run-only         Validate and map everything, but never commit
  -h, --help             Show this help
EOF
}

while (($#)); do
  case "$1" in
    --test|--production) shift ;;
    --config) config_file="${2:-}"; shift 2 ;;
    --backup) backup_file="${2:-}"; shift 2 ;;
    --owner) requested_owner_mappings+=("${2:-}"); shift 2 ;;
    --dry-run-only) dry_run_only=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

fail() { printf '[build-restore:%s] %s\n' "$target_environment" "$*" >&2; exit 1; }
validate_username() {
  local username="$1"
  [[ ${#username} -ge 3 && ${#username} -le 80 ]] || return 1
  [[ ! "$username" =~ [[:space:]] && ! "$username" =~ [[:cntrl:]] ]]
}

if [[ -z "$backup_file" ]]; then
  mapfile -t candidates < <(find "$ROOT_DIR/backups" -maxdepth 1 -type f \
    -name 'rbf-builds-partial-*.sql' -print | sort)
  ((${#candidates[@]} > 0)) || fail 'No portable build backup was found in backups/.'
  if ((${#candidates[@]} == 1)); then
    backup_file="${candidates[0]}"
  elif [[ -t 0 && -t 1 ]]; then
    printf 'Available build backups:\n'
    for index in "${!candidates[@]}"; do
      printf '  %d) %s\n' "$((index + 1))" "$(basename "${candidates[$index]}")"
    done
    read -r -p 'Selection: ' selection
    [[ "$selection" =~ ^[0-9]+$ && "$selection" -ge 1 && "$selection" -le "${#candidates[@]}" ]] \
      || fail 'Invalid backup selection.'
    backup_file="${candidates[$((selection - 1))]}"
  else
    fail 'Multiple backups exist; select one with --backup.'
  fi
fi
[[ "$backup_file" == /* ]] || backup_file="$ROOT_DIR/$backup_file"
[[ -f "$backup_file" && ! -L "$backup_file" ]] || fail "Backup is missing or unsafe: $backup_file"
[[ "$(basename "$backup_file")" =~ ^rbf-builds-partial-[A-Za-z0-9._-]+\.sql$ ]] \
  || fail 'Backup filename must match rbf-builds-partial-*.sql.'
grep -Fq '\set ON_ERROR_STOP on' "$backup_file" || fail 'Backup does not enforce ON_ERROR_STOP.'
grep -Fq 'DRY RUN successful; rolling back all changes.' "$backup_file" \
  || fail 'Backup does not contain the required transactional dry-run boundary.'
expected_builds="$(sed -nE 's/^--[[:space:]]+([0-9]+)[[:space:]]+builds$/\1/p' "$backup_file" | head -n1)"
expected_slots="$(sed -nE 's/^--[[:space:]]+([0-9]+)[[:space:]]+build slots$/\1/p' "$backup_file" | head -n1)"
expected_classifications="$(sed -nE 's/^--[[:space:]]+([0-9]+)[[:space:]]+build classifications$/\1/p' "$backup_file" | head -n1)"
[[ "$expected_builds" =~ ^[1-9][0-9]*$ && "$expected_slots" =~ ^[1-9][0-9]*$ \
  && "$expected_classifications" =~ ^[1-9][0-9]*$ ]] \
  || fail 'Backup does not declare positive expected logical row counts.'

declare -A requested_targets=()
for mapping in "${requested_owner_mappings[@]}"; do
  [[ "$mapping" == *=* ]] || fail "Invalid owner mapping (expected SOURCE=TARGET): $mapping"
  source_username="${mapping%%=*}"; target_username="${mapping#*=}"
  [[ -n "$source_username" && -n "$target_username" ]] || fail "Incomplete owner mapping: $mapping"
  validate_username "$target_username" || fail "Invalid target username for $source_username."
  requested_targets["$source_username"]="$target_username"
done

mapfile -t owner_contract < <(sed -nE \
  "s/^[[:space:]]*\('([^']+)',[[:space:]]*:'([A-Za-z_][A-Za-z0-9_]*)'\)[,;]?$/\1|\2/p" \
  "$backup_file")
((${#owner_contract[@]} > 0)) || fail 'No owner mapping contract was found in the backup.'

declare -a owner_variables=()
declare -A known_sources=()
printf '[build-restore:%s] Backup: %s\n' "$target_environment" "$(basename "$backup_file")"
for contract in "${owner_contract[@]}"; do
  source_username="${contract%%|*}"; variable="${contract#*|}"
  known_sources["$source_username"]=1
  target_username="${requested_targets[$source_username]:-$source_username}"
  if [[ -t 0 && -t 1 && -z "${requested_targets[$source_username]+set}" ]]; then
    read -r -p "Map owner '$source_username' to target username [$target_username]: " answer
    target_username="${answer:-$target_username}"
  fi
  validate_username "$target_username" || fail "Invalid target username for $source_username."
  owner_variables+=("$variable=$target_username")
  printf '[build-restore:%s] Owner mapping: %s -> %s\n' \
    "$target_environment" "$source_username" "$target_username"
done
for source_username in "${!requested_targets[@]}"; do
  [[ -n "${known_sources[$source_username]:-}" ]] \
    || fail "Owner mapping does not exist in this backup: $source_username"
done

[[ -f "$config_file" && ! -L "$config_file" ]] || fail "Origin configuration is missing or unsafe: $config_file"
[[ "$(stat -c '%a' "$config_file")" == 600 ]] || fail "Origin configuration must have mode 600: $config_file"
[[ "$(stat -c '%u' "$config_file")" == "$(id -u)" ]] || fail 'Origin configuration is not owned by the invoking user.'
# shellcheck disable=SC1090
source "$config_file"
host="${RBF_DEPLOY_HOST:-}"; user="${RBF_DEPLOY_USER:-rbfadmin}"
port="${RBF_DEPLOY_PORT:-22}"; identity_file="${RBF_DEPLOY_IDENTITY_FILE:-}"
install_root="${RBF_DEPLOY_INSTALL_ROOT:-/srv/rbf}"
if [[ -z "$identity_file" && -n "${HOME:-}" && -f "$HOME/.ssh/$user" ]]; then
  identity_file="$HOME/.ssh/$user"
fi
[[ -n "$host" && ! "$host" =~ [[:space:]] ]] || fail 'Invalid or missing deployment host.'
[[ "$user" =~ ^[A-Za-z_][A-Za-z0-9_.-]{2,39}$ ]] || fail 'Invalid SSH user.'
[[ "$port" =~ ^[0-9]+$ && "$port" -le 65535 ]] || fail 'Invalid SSH port.'
[[ "$install_root" == /* && "$install_root" != / ]] || fail 'Installation root must be a non-root absolute path.'
[[ -z "$identity_file" || -f "$identity_file" ]] || fail "SSH identity is missing: $identity_file"
for command in ssh scp sha256sum tee; do
  command -v "$command" >/dev/null 2>&1 || fail "Required command is missing: $command"
done

ssh_args=(-o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -p "$port")
scp_args=(-o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=10 -P "$port")
if [[ -n "$identity_file" ]]; then ssh_args+=(-i "$identity_file"); scp_args+=(-i "$identity_file"); fi
stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
remote_upload="/tmp/rbf-build-restore-$stamp.sql"
remote_helper="/tmp/rbf-build-restore-$stamp-helper.sh"
checksum="$(sha256sum "$backup_file" | awk '{print $1}')"
helper_checksum="$(sha256sum "$SCRIPT_DIR/restore-builds-remote.sh" | awk '{print $1}')"
remote_output_capture=""
cleanup() {
  [[ -z "$remote_output_capture" ]] || rm -f -- "$remote_output_capture"
  cleanup_command=(rm -f -- "$remote_upload" "$remote_helper")
  cleanup_line=""; for word in "${cleanup_command[@]}"; do printf -v quoted ' %q' "$word"; cleanup_line+="$quoted"; done
  ssh "${ssh_args[@]}" "$user@$host" "$cleanup_line" >/dev/null 2>&1 || true
}
trap cleanup EXIT

printf '[build-restore:%s] Uploading the immutable migration artifact and remote helper.\n' "$target_environment"
scp "${scp_args[@]}" "$backup_file" "$user@$host:$remote_upload"
scp "${scp_args[@]}" "$SCRIPT_DIR/restore-builds-remote.sh" "$user@$host:$remote_helper"

run_remote() {
  local mode="$1" remote_line="" remote_output="" marker quoted word
  local remote_command=(sudo -n /usr/bin/env bash "$remote_helper"
    --helper-sha256 "$helper_checksum" --install-root "$install_root" --upload "$remote_upload"
    --artifact-name "$(basename "$backup_file")" --sha256 "$checksum" --mode "$mode"
    --expected-builds "$expected_builds" --expected-slots "$expected_slots"
    --expected-classifications "$expected_classifications")
  for word in "${owner_variables[@]}"; do remote_command+=(--owner-variable "$word"); done
  for word in "${remote_command[@]}"; do printf -v quoted ' %q' "$word"; remote_line+="$quoted"; done
  # All arguments are validated and shell-quoted above. The helper is a separate,
  # checksummed remote file so Docker cannot consume its program text from SSH stdin.
  # shellcheck disable=SC2029
  remote_output_capture="$(mktemp /tmp/rbf-build-restore-output.XXXXXX)"
  if ! ssh "${ssh_args[@]}" "$user@$host" "$remote_line" </dev/null \
      | tee "$remote_output_capture"; then
    rm -f -- "$remote_output_capture"
    remote_output_capture=""
    return 1
  fi
  remote_output="$(<"$remote_output_capture")"
  rm -f -- "$remote_output_capture"
  remote_output_capture=""
  if [[ "$mode" == dry-run ]]; then
    marker='[build-restore] Dry run passed; transaction was rolled back.'
  else
    marker='[build-restore] Committed import passed all post-import checks.'
  fi
  [[ "$remote_output" == *"$marker"* ]] \
    || fail "Remote $mode did not emit its required completion marker."
}

printf '[build-restore:%s] Running mandatory transactional dry run.\n' "$target_environment"
run_remote dry-run
if [[ "$dry_run_only" == true ]]; then
  printf '[build-restore:%s] Dry run passed; no target data was changed.\n' "$target_environment"
  exit 0
fi
[[ -t 0 && -t 1 ]] || fail 'Dry run passed. Re-run interactively to authorize the committed restore.'

if [[ "$target_environment" == production ]]; then
  read -r -p "Type 'restore production builds' to create a safety backup and commit: " confirmation
  [[ "$confirmation" == 'restore production builds' ]] || fail 'Production restore cancelled.'
else
  read -r -p "Type 'restore test builds' to create a safety backup and commit: " confirmation
  [[ "$confirmation" == 'restore test builds' ]] || fail 'Test restore cancelled.'
fi
run_remote commit
printf '[build-restore:%s] Build restore completed and verified.\n' "$target_environment"
