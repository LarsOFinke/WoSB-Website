#!/usr/bin/env bash
set -Eeuo pipefail

# Update only the managed Recovery Tool code. Profiles, keys and downloaded
# backups live outside the repository and are deliberately never touched.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$ROOT_DIR/tools/recovery-tool/src/rbf_recovery_tool"
INSTALL_ROOT="/opt/rbf-recovery-tool"
INSTALL_DIR="$INSTALL_ROOT/src/rbf_recovery_tool"
PROFILES_FILE="/etc/rbf-recovery-tool/RBF Recovery Tool/profiles.json"
STAGING_DIR=""
OLD_DIR=""

cleanup() {
  if [[ -n "$STAGING_DIR" && -d "$STAGING_DIR" ]]; then
    rm -rf -- "$STAGING_DIR"
  fi
  if [[ -n "$OLD_DIR" && -d "$OLD_DIR" ]]; then
    if [[ ! -e "$INSTALL_DIR" ]]; then
      mv -- "$OLD_DIR" "$INSTALL_DIR"
    else
      rm -rf -- "$OLD_DIR"
    fi
  fi
}
trap cleanup EXIT

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

[[ "$EUID" -eq 0 ]] || die "run as root: sudo ./update-recovery-tool.sh"
[[ -d "$SOURCE_DIR" ]] || die "Recovery Tool source directory is missing: $SOURCE_DIR"
[[ -x /usr/bin/python3 ]] || die "Python 3 is missing: /usr/bin/python3"
[[ -x /bin/systemctl ]] || die "systemctl is missing: automatic sync timers cannot be installed"
install -d -o root -g root -m 0755 "$INSTALL_ROOT/src"

shopt -s nullglob
source_files=("$SOURCE_DIR"/*.py)
(( ${#source_files[@]} > 0 )) || die "No Recovery Tool Python sources were found."

STAGING_DIR="$(mktemp -d "$INSTALL_ROOT/.recovery-tool-update.XXXXXX")"
install -d -o root -g root -m 0755 "$STAGING_DIR/src/rbf_recovery_tool"
install -o root -g root -m 0644 "${source_files[@]}" "$STAGING_DIR/src/rbf_recovery_tool/"

env PYTHONPATH="$STAGING_DIR/src" PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -m compileall -q "$STAGING_DIR/src"

OLD_DIR="$INSTALL_ROOT/src/rbf_recovery_tool.previous.$$"
if [[ -e "$INSTALL_DIR" ]]; then
  mv -- "$INSTALL_DIR" "$OLD_DIR"
fi
mv -- "$STAGING_DIR/src/rbf_recovery_tool" "$INSTALL_DIR"
STAGING_DIR=""

install_sync_units() {
  [[ -f "$PROFILES_FILE" && ! -L "$PROFILES_FILE" ]] || return 0
  mapfile -t profiles < <(/usr/bin/python3 - "$PROFILES_FILE" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for target, profile in payload.get("profiles", {}).items():
    if target not in {"test", "production"} or not isinstance(profile, dict):
        continue
    storage = str(profile.get("destination_directory") or "")
    if storage != f"/backups/wosb/{target}":
        continue
    print(f"{target}\t{storage}")
PY
  )
  ((${#profiles[@]} > 0)) || return 0
  for record in "${profiles[@]}"; do
    IFS=$'\t' read -r target storage <<< "$record"
    install -d -m 0755 /etc/systemd/system
    cat > "/etc/systemd/system/rbf-recovery-controller-${target}.service" <<EOF_SERVICE
[Unit]
Description=RBF ${target} automatic published-export sync
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/flock --wait 30 /run/rbf-recovery-${target}/controller.lock /usr/local/bin/rbf-recovery-tool sync --target ${target} --quiet
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
RuntimeDirectory=rbf-recovery-${target}
RuntimeDirectoryMode=0750
ReadWritePaths=${storage}
ProtectHome=true
EOF_SERVICE
    cat > "/etc/systemd/system/rbf-recovery-controller-${target}.timer" <<EOF_TIMER
[Unit]
Description=RBF ${target} automatic published-export sync timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Persistent=true
Unit=rbf-recovery-controller-${target}.service

[Install]
WantedBy=timers.target
EOF_TIMER
  done
  systemctl daemon-reload
  for record in "${profiles[@]}"; do
    target="${record%%$'\t'*}"
    systemctl enable --now "rbf-recovery-controller-${target}.timer"
  done
  printf 'OK: Automatic published-export sync enabled for %s\n' "$(printf '%s\n' "${profiles[@]}" | cut -f1 | paste -sd, -)"
}

install_sync_units

printf 'OK: Recovery Tool code updated from %s\n' "$SOURCE_DIR"
env PYTHONPATH="$INSTALL_ROOT/src" PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -m rbf_recovery_tool targets
