#!/usr/bin/env bash
set -Eeuo pipefail

die() { echo "[rollback] $*" >&2; exit 1; }
[[ "$EUID" -eq 0 ]] || die "Release rollback requires root."
install_root="${RBF_INSTALL_ROOT:-/srv/rbf}"
[[ "$install_root" == /* && "$install_root" != / ]] || die "Install root must be a specific absolute directory."
shared="$install_root/shared"; state="$shared/deployment-state.json"
[[ -f "$state" && ! -L "$state" ]] || die "No deployment rollback metadata is available."
install -d -m 0700 "$shared/locks"
exec 9>"$shared/locks/release.lock"; flock 9

mapfile -d '' -t values < <(python3 - "$state" <<'PY'
import json, sys
payload=json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("current_release","previous_release","rollback_postgres","rollback_files","previous_environment"):
    print(payload.get(key) or "", end="\0")
PY
)
current="${values[0]:-}"; previous="${values[1]:-}"; postgres="${values[2]:-}"
files="${values[3]:-}"; previous_env="${values[4]:-}"
[[ -n "$previous" && -d "$previous" && "$previous" == "$install_root/releases/"* ]] \
  || die "Rollback metadata does not reference an available previous release."
[[ "$(readlink -f "$install_root/current")" == "$current" ]] \
  || die "Active release does not match rollback metadata."
[[ -f "$postgres" && -f "$postgres.sha256" ]] || die "Coordinated rollback database backup is unavailable."
[[ -f "$files" && -f "$files.sha256" ]] || die "Coordinated rollback file backup is unavailable."

install -d -m 0700 "$shared/data/control/run"
exec 8>"$shared/data/control/run/update.lock"; flock 8
"$install_root/current/infrastructure/scripts/services/stop.sh"
ln -sfn "$previous" "$install_root/.current.rollback"
mv -Tf "$install_root/.current.rollback" "$install_root/current"
if [[ -n "$previous_env" ]]; then
  [[ -f "$previous_env" ]] || die "Previous environment snapshot is unavailable."
  install -m 0600 "$previous_env" "$shared/.env"
fi
RBF_SYSTEMD_INFRA_DIR="$install_root/current/infrastructure" \
  "$install_root/current/infrastructure/scripts/deployment/install-systemd.sh"
systemctl restart rbf-hub.service
"$install_root/current/infrastructure/scripts/backup/restore-data.sh" --yes "$files"
RBF_UPDATE_LOCK_HELD=true "$install_root/current/infrastructure/scripts/backup/restore-postgres.sh" "$postgres"
"$install_root/current/infrastructure/scripts/checks/smoke-test.sh"

rolled_back="$shared/deployments/rolled-back-$(date -u +%Y%m%dT%H%M%SZ).json"
install -m 0600 "$state" "$rolled_back"
rm -f "$state"
version="$(cat "$install_root/current/VERSION")"
artifact="$shared/release-artifacts/rbf-deployment-$version.tar.gz"
if [[ -f "$artifact" ]]; then
  install -m 0600 "$artifact" "$shared/release-artifacts/current.tar.gz"
  (cd "$shared/release-artifacts" && sha256sum current.tar.gz > current.tar.gz.sha256)
fi
printf '%s\n' "$version" > "$shared/current-version"
chmod 0644 "$shared/current-version"
echo "[rollback] Restored release $version and its coordinated pre-deployment data point."
