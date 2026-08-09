#!/usr/bin/env bash
set -Eeuo pipefail

install_root=""; upload=""; artifact_name=""; expected_sha=""; helper_sha=""; mode=""
expected_builds=""; expected_slots=""; expected_classifications=""
declare -a owner_variables=()
while (($#)); do
  case "$1" in
    --helper-sha256) helper_sha="${2:-}"; shift 2 ;;
    --install-root) install_root="${2:-}"; shift 2 ;;
    --upload) upload="${2:-}"; shift 2 ;;
    --artifact-name) artifact_name="${2:-}"; shift 2 ;;
    --sha256) expected_sha="${2:-}"; shift 2 ;;
    --mode) mode="${2:-}"; shift 2 ;;
    --expected-builds) expected_builds="${2:-}"; shift 2 ;;
    --expected-slots) expected_slots="${2:-}"; shift 2 ;;
    --expected-classifications) expected_classifications="${2:-}"; shift 2 ;;
    --owner-variable) owner_variables+=("${2:-}"); shift 2 ;;
    *) echo '[build-restore] Invalid remote restore option.' >&2; exit 2 ;;
  esac
done

die() { printf '[build-restore] %s\n' "$*" >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || die 'Remote build restore requires root privileges.'
helper_path="${BASH_SOURCE[0]}"
[[ "$helper_path" =~ ^/tmp/rbf-build-restore-[A-Za-z0-9-]+-helper\.sh$ ]] \
  || die 'Unsafe remote helper path.'
[[ "$helper_sha" =~ ^[a-f0-9]{64}$ ]] || die 'Invalid remote helper checksum.'
[[ -f "$helper_path" && ! -L "$helper_path" ]] || die 'Remote helper is missing or unsafe.'
actual_helper_sha="$(sha256sum "$helper_path" | awk '{print $1}')"
[[ "$actual_helper_sha" == "$helper_sha" ]] || die 'Remote helper checksum mismatch.'
[[ "$install_root" == /* && "$install_root" != / ]] || die 'Unsafe installation root.'
[[ "$upload" =~ ^/tmp/rbf-build-restore-[A-Za-z0-9-]+\.sql$ ]] || die 'Unsafe upload path.'
[[ "$artifact_name" =~ ^rbf-builds-partial-[A-Za-z0-9._-]+\.sql$ ]] || die 'Unsafe artifact name.'
[[ "$expected_sha" =~ ^[a-f0-9]{64}$ ]] || die 'Invalid artifact checksum.'
[[ "$mode" == dry-run || "$mode" == commit ]] || die 'Mode must be dry-run or commit.'
[[ "$expected_builds" =~ ^[1-9][0-9]*$ ]] || die 'Invalid expected build count.'
[[ "$expected_slots" =~ ^[1-9][0-9]*$ ]] || die 'Invalid expected slot count.'
[[ "$expected_classifications" =~ ^[1-9][0-9]*$ ]] || die 'Invalid expected classification count.'
[[ -f "$upload" && ! -L "$upload" ]] || die 'Uploaded migration artifact is missing or unsafe.'
actual_sha="$(sha256sum "$upload" | awk '{print $1}')"
[[ "$actual_sha" == "$expected_sha" ]] || die 'Uploaded migration artifact checksum mismatch.'
[[ -d "$install_root/current/infrastructure" ]] || die 'Current RBF installation is missing.'

for assignment in "${owner_variables[@]}"; do
  [[ "$assignment" =~ ^[A-Za-z_][A-Za-z0-9_]*=.+$ ]] || die 'Invalid owner variable assignment.'
  value="${assignment#*=}"
  [[ ${#value} -ge 3 && ${#value} -le 80 && ! "$value" =~ [[:space:]] && ! "$value" =~ [[:cntrl:]] ]] \
    || die 'Invalid target owner username.'
done

imports="$install_root/shared/imports"
artifact="$imports/$artifact_name"
install -d -o root -g root -m 0750 "$imports"
if [[ -e "$artifact" ]]; then
  [[ -f "$artifact" && ! -L "$artifact" ]] || die 'Existing migration artifact is unsafe.'
  installed_sha="$(sha256sum "$artifact" | awk '{print $1}')"
  [[ "$installed_sha" == "$expected_sha" ]] || die 'A different artifact already uses this backup filename.'
else
  install -o root -g root -m 0600 "$upload" "$artifact"
fi
[[ -f "$artifact" && ! -L "$artifact" ]] || die "Installed migration artifact is missing: $artifact"
installed_sha="$(sha256sum "$artifact" | awk '{print $1}')"
[[ "$installed_sha" == "$expected_sha" ]] || die 'Installed migration artifact checksum mismatch.'
printf '[build-restore] Installed artifact: %s (sha256=%s)\n' "$artifact" "$installed_sha"

cd "$install_root/current"
# shellcheck source=../lib/docker.sh
source infrastructure/scripts/lib/docker.sh
require_command flock
backup_result=""
cleanup_result() { [[ -z "$backup_result" ]] || rm -f -- "$backup_result"; }
trap cleanup_result EXIT
run_dir="$INFRA_DIR/data/control/run"
install -d -m 0700 "$run_dir"
exec 9>"$run_dir/update.lock"
flock 9
ensure_postgres_service

psql_arguments=(-v ON_ERROR_STOP=1)
if [[ "$mode" == dry-run ]]; then
  psql_arguments+=(-v dry_run=1)
else
  printf '[build-restore] Creating scoped PostgreSQL safety dump before import.\n'
  exec 8>"$run_dir/backup.lock"
  flock 8
  backup_result="$(mktemp "$run_dir/build-restore-backup.XXXXXX")"
  if ! BACKUP_REASON=pre-build-restore BACKUP_CONSISTENCY_MODE=postgres-snapshot \
      BACKUP_RESULT_FILE="$backup_result" \
      /usr/bin/env bash infrastructure/scripts/backup/backup-postgres.sh; then
    die 'Scoped PostgreSQL safety dump failed; build import was not started.'
  fi
  safety_backup="$(<"$backup_result")"
  rm -f -- "$backup_result"
  backup_result=""
  [[ -f "$safety_backup" && ! -L "$safety_backup" && -f "${safety_backup}.sha256" ]] \
    || die 'Scoped PostgreSQL safety dump was not committed correctly.'
  printf '[build-restore] Safety dump ready: %s\n' "$safety_backup"
  psql_arguments+=(-v dry_run=0)
fi
for assignment in "${owner_variables[@]}"; do psql_arguments+=(-v "$assignment"); done

printf '[build-restore] Resolving owners and current build-catalog references (%s).\n' "$mode"
postgres_sql "${psql_arguments[@]}" -f - < "$artifact"
if [[ "$mode" == dry-run ]]; then
  printf '[build-restore] Dry run passed; transaction was rolled back.\n'
else
  actual_counts="$(postgres_sql -Atqc '
    select
      (select count(*) from public.builds),
      (select count(*) from public.build_slots),
      (select count(*) from public.build_classifications);
  ')"
  IFS='|' read -r actual_builds actual_slots actual_classifications <<<"$actual_counts"
  [[ "$actual_builds" =~ ^[0-9]+$ && "$actual_slots" =~ ^[0-9]+$ \
    && "$actual_classifications" =~ ^[0-9]+$ ]] \
    || die "Could not read post-commit logical row counts: $actual_counts"
  (( actual_builds >= expected_builds )) \
    || die "Post-commit build count $actual_builds is below expected $expected_builds."
  (( actual_slots >= expected_slots )) \
    || die "Post-commit slot count $actual_slots is below expected $expected_slots."
  (( actual_classifications >= expected_classifications )) \
    || die "Post-commit classification count $actual_classifications is below expected $expected_classifications."
  printf '[build-restore] Post-commit counts: builds=%s slots=%s classifications=%s\n' \
    "$actual_builds" "$actual_slots" "$actual_classifications"
  printf '[build-restore] Committed import passed all post-import checks.\n'
fi
