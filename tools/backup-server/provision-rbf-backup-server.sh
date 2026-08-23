#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "This provisioning requires root privileges." >&2; exit 1; }

REQUEST=""; RESULT=""; RETENTION_DAYS=30; SKIP_PACKAGE_INSTALL=false
while (($#)); do
  case "$1" in
    --request) REQUEST="$2"; shift 2 ;;
    --result) RESULT="$2"; shift 2 ;;
    --retention-days) RETENTION_DAYS="$2"; shift 2 ;;
    --skip-package-install) SKIP_PACKAGE_INSTALL=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[[ -f "$REQUEST" && ! -L "$REQUEST" && -n "$RESULT" ]] || {
  echo "--request and --result are required." >&2
  exit 2
}
[[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]] && ((RETENTION_DAYS <= 3650)) || {
  echo "Invalid retention period." >&2
  exit 2
}

readarray -t fields < <(python3 - "$REQUEST" <<'PY'
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
if payload.get("schema_version") != 1 or payload.get("kind") != "rbf-backup-enrollment-request":
    raise SystemExit("Unsupported enrollment request.")
environment = str(payload.get("deployment_environment") or "").strip().lower()
enrollment_id = str(payload.get("enrollment_id") or "").strip()
username = str(payload.get("requested_controller_username") or "").strip()
storage = str(payload.get("requested_storage_directory") or "").strip().rstrip("/")
host = str(payload.get("website_host") or "").strip().lower()
port = payload.get("website_ssh_port")
host_key = str(payload.get("website_host_key") or "").strip()
fingerprint = str(payload.get("website_host_key_fingerprint") or "").strip()
encoded_tool = str(payload.get("recovery_tool_base64") or "")
tool_sha = str(payload.get("recovery_tool_sha256") or "")
if environment not in {"test", "production"}:
    raise SystemExit("Invalid deployment environment.")
if not re.fullmatch(r"[A-Za-z0-9_-]{24,128}", enrollment_id):
    raise SystemExit("Invalid enrollment ID.")
if username != f"rbf-backup-controller-{environment}":
    raise SystemExit("Controller identity does not match the environment.")
if storage != f"/backups/wosb/{environment}":
    raise SystemExit("Storage directory does not match the environment.")
if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", host):
    raise SystemExit("Invalid website SSH host.")
if not isinstance(port, int) or not 1 <= port <= 65535:
    raise SystemExit("Invalid website SSH port.")
if not re.fullmatch(r"(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+", host_key):
    raise SystemExit("Invalid website SSH host key.")
if not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{40,64}", fingerprint):
    raise SystemExit("Invalid website host-key fingerprint.")
tool = base64.b64decode(encoded_tool, validate=True)
if not tool or len(tool) > 1024 * 1024 or hashlib.sha256(tool).hexdigest() != tool_sha:
    raise SystemExit("Embedded Recovery Tool verification failed.")
for value in (enrollment_id, environment, username, storage, host, str(port), host_key, fingerprint, encoded_tool, tool_sha):
    print(value)
PY
)
(( ${#fields[@]} == 10 )) || { echo "Enrollment request is incomplete." >&2; exit 1; }
ENROLLMENT_ID="${fields[0]}"; ENVIRONMENT="${fields[1]}"; USERNAME="${fields[2]}"
STORAGE="${fields[3]}"; WEBSITE_HOST="${fields[4]}"; WEBSITE_PORT="${fields[5]}"
WEBSITE_HOST_KEY="${fields[6]}"; WEBSITE_FINGERPRINT="${fields[7]}"
TOOL_BASE64="${fields[8]}"; TOOL_SHA="${fields[9]}"

if [[ "$SKIP_PACKAGE_INSTALL" != true ]] && {
  ! /usr/bin/python3 -c 'import paramiko' >/dev/null 2>&1 || ! command -v age-keygen >/dev/null 2>&1
}; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y python3-paramiko age openssh-client
fi
for command_name in python3 ssh-keygen age-keygen flock systemctl; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "Required tool is missing: $command_name" >&2; exit 1; }
done
/usr/bin/python3 -c 'import paramiko' >/dev/null 2>&1 || {
  echo "The Python Paramiko package is required." >&2
  exit 1
}

STATE_ROOT="/etc/rbf-recovery-tool"
TARGET_ROOT="$STATE_ROOT/$ENVIRONMENT"
TOOL_ROOT="/opt/rbf-recovery-tool"
KEY="$TARGET_ROOT/controller-ed25519"
AGE_IDENTITY="$TARGET_ROOT/recovery-age-identity.txt"
KNOWN_HOSTS="$TARGET_ROOT/known_hosts"
STATE_FILE="$TARGET_ROOT/state.json"
install -d -m 0700 -o root -g root "$STATE_ROOT" "$TARGET_ROOT"
install -d -m 0755 -o root -g root "$TOOL_ROOT" "$TOOL_ROOT/src"
if [[ -f "$STATE_FILE" ]]; then
  python3 - "$STATE_FILE" "$ENVIRONMENT" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
if payload.get("managed_by") != "rbf-recovery-controller" or payload.get("deployment_environment") != sys.argv[2]:
    raise SystemExit("Existing Recovery Tool state is not managed for this environment.")
PY
elif [[ -e "$KEY" || -e "$KEY.pub" || -e "$AGE_IDENTITY" || -e "$KNOWN_HOSTS" ]]; then
  echo "Existing controller key material has no matching managed state." >&2
  exit 1
fi
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -q -t ed25519 -N '' -C "$USERNAME" -f "$KEY"
fi
if [[ ! -f "$AGE_IDENTITY" ]]; then
  age-keygen -o "$AGE_IDENTITY" >/dev/null
fi
[[ -f "$KEY" && ! -L "$KEY" && -f "$KEY.pub" && ! -L "$KEY.pub" && -f "$AGE_IDENTITY" && ! -L "$AGE_IDENTITY" ]] || {
  echo "Unsafe or incomplete controller key material." >&2
  exit 1
}
AGE_RECIPIENT="$(age-keygen -y "$AGE_IDENTITY")"
CONTROLLER_PUBLIC_KEY="$(cat "$KEY.pub")"
FINGERPRINT_FILE="$(mktemp)"
trap 'rm -f "$FINGERPRINT_FILE"' EXIT
printf '%s\n' "$WEBSITE_HOST_KEY" > "$FINGERPRINT_FILE"
ACTUAL_FINGERPRINT="$(ssh-keygen -lf "$FINGERPRINT_FILE" -E sha256 | awk '{print $2}')"
[[ "$ACTUAL_FINGERPRINT" == "$WEBSITE_FINGERPRINT" ]] || {
  echo "Website host key does not match its pinned fingerprint." >&2
  exit 1
}
if [[ "$WEBSITE_PORT" == 22 ]]; then HOST_TOKEN="$WEBSITE_HOST"; else HOST_TOKEN="[$WEBSITE_HOST]:$WEBSITE_PORT"; fi
printf '%s %s\n' "$HOST_TOKEN" "$WEBSITE_HOST_KEY" > "$KNOWN_HOSTS"
chmod 0600 "$KEY" "$AGE_IDENTITY" "$KNOWN_HOSTS"
chmod 0644 "$KEY.pub"
python3 - "$STATE_FILE" "$ENROLLMENT_ID" "$ENVIRONMENT" "$WEBSITE_HOST" "$WEBSITE_PORT" "$STORAGE" "$RETENTION_DAYS" <<'PY'
import json, os, sys, tempfile
from pathlib import Path
path = Path(sys.argv[1])
payload = {
    "schema_version": 1, "managed_by": "rbf-recovery-controller",
    "enrollment_id": sys.argv[2], "deployment_environment": sys.argv[3],
    "website_host": sys.argv[4], "website_port": int(sys.argv[5]),
    "storage_directory": sys.argv[6], "retention_days": int(sys.argv[7]),
}
fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
with os.fdopen(fd, "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True); handle.write("\n")
os.chmod(temporary, 0o600); os.replace(temporary, path)
PY

python3 - "$TOOL_BASE64" "$TOOL_SHA" "$TOOL_ROOT/src" <<'PY'
import base64
import hashlib
import io
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

content = base64.b64decode(sys.argv[1], validate=True)
if hashlib.sha256(content).hexdigest() != sys.argv[2]:
    raise SystemExit("Recovery Tool checksum changed during provisioning.")
target = Path(sys.argv[3])
stage = Path(tempfile.mkdtemp(prefix="rbf-recovery-tool-", dir=target.parent))
try:
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            if member.issym() or member.islnk() or member.isdev() or path.is_absolute() or ".." in path.parts:
                raise SystemExit("Unsafe Recovery Tool archive member.")
        archive.extractall(stage, members=members)
    old = target.with_name(target.name + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if target.exists():
        target.rename(old)
    stage.rename(target)
    shutil.rmtree(old, ignore_errors=True)
except Exception:
    shutil.rmtree(stage, ignore_errors=True)
    raise
PY
find "$TOOL_ROOT/src" -type d -exec chmod 0755 {} +
find "$TOOL_ROOT/src" -type f -exec chmod 0644 {} +
chown -R root:root "$TOOL_ROOT"
install -d -m 0700 -o root -g root "$STORAGE"

CONFIG_DIR="$STATE_ROOT/RBF Recovery Tool"
install -d -m 0700 -o root -g root "$CONFIG_DIR"
python3 - "$CONFIG_DIR/profiles.json" "$ENVIRONMENT" "$WEBSITE_HOST" "$WEBSITE_PORT" "$USERNAME" "$STORAGE" "$KEY" "$AGE_IDENTITY" "$WEBSITE_FINGERPRINT" "$ENROLLMENT_ID" "$RETENTION_DAYS" <<'PY'
import json
import os
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
target = sys.argv[2]
payload = {"schema_version": 2, "active_target": target, "profiles": {}}
if path.is_file():
    existing = json.loads(path.read_text())
    if isinstance(existing, dict) and existing.get("schema_version") == 2:
        payload = existing
payload["active_target"] = target
payload.setdefault("profiles", {})[target] = {
    "host": sys.argv[3], "port": int(sys.argv[4]), "username": sys.argv[5],
    "remote_directory": "/exports", "destination_directory": sys.argv[6],
    "ssh_key_path": sys.argv[7], "age_identity_path": sys.argv[8],
    "host_fingerprint": sys.argv[9], "enrollment_id": sys.argv[10],
    "retention_days": int(sys.argv[11]),
}
fd, temporary = tempfile.mkstemp(prefix=".profiles.", dir=path.parent)
with os.fdopen(fd, "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.chmod(temporary, 0o600)
os.replace(temporary, path)
PY

cat > /usr/local/bin/rbf-recovery-tool <<'EOF_TOOL'
#!/usr/bin/env bash
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "ERROR: rbf-recovery-tool must be run as root (use: sudo rbf-recovery-tool ...)." >&2
  exit 77
fi
export XDG_CONFIG_HOME=/etc/rbf-recovery-tool
export PYTHONPATH=/opt/rbf-recovery-tool/src
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -m rbf_recovery_tool "$@"
EOF_TOOL
chmod 0755 /usr/local/bin/rbf-recovery-tool
chown root:root /usr/local/bin/rbf-recovery-tool

cat > "/etc/systemd/system/rbf-recovery-controller-${ENVIRONMENT}.service" <<EOF_SERVICE
[Unit]
Description=RBF ${ENVIRONMENT} backup-controller pull and verification
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/flock --wait 30 /run/rbf-recovery-${ENVIRONMENT}/controller.lock /usr/local/bin/rbf-recovery-tool sync --target ${ENVIRONMENT} --quiet
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
RuntimeDirectory=rbf-recovery-${ENVIRONMENT}
RuntimeDirectoryMode=0750
ReadWritePaths=${STORAGE}
ProtectHome=true
EOF_SERVICE
cat > "/etc/systemd/system/rbf-recovery-trigger-${ENVIRONMENT}.service" <<EOF_TRIGGER_SERVICE
[Unit]
Description=Trigger and pull the daily ${ENVIRONMENT} backup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/flock --wait 30 /run/rbf-recovery-${ENVIRONMENT}/controller.lock /usr/local/bin/rbf-recovery-tool run --target ${ENVIRONMENT} --quiet
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
RuntimeDirectory=rbf-recovery-${ENVIRONMENT}
RuntimeDirectoryMode=0750
ReadWritePaths=${STORAGE}
ProtectHome=true
EOF_TRIGGER_SERVICE
systemctl daemon-reload
systemctl disable --now "rbf-recovery-controller-${ENVIRONMENT}.timer" "rbf-recovery-trigger-${ENVIRONMENT}.timer" >/dev/null 2>&1 || true
rm -f "/etc/systemd/system/rbf-recovery-controller-${ENVIRONMENT}.timer" "/etc/systemd/system/rbf-recovery-trigger-${ENVIRONMENT}.timer"
systemctl daemon-reload

# Remove the superseded managed push/ingest control plane only after the new
# controller is installed. Existing backup data is deliberately preserved.
LEGACY_STATE="/etc/rbf-backup-server/rbf-backup.json"
if [[ -f "$LEGACY_STATE" ]] && python3 - "$LEGACY_STATE" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
raise SystemExit(0 if payload.get("managed_by") == "rbf-recovery-tool" else 1)
PY
then
  for legacy_unit in \
    "rbf-backup-ingest-${ENVIRONMENT}.path" \
    "rbf-backup-ingest-${ENVIRONMENT}.timer" \
    "rbf-backup-ingest-${ENVIRONMENT}.service" \
    "rbf-backup-retention-${ENVIRONMENT}.timer" \
    "rbf-backup-retention-${ENVIRONMENT}.service" \
    "rbf-backup-tunnel-${ENVIRONMENT}.service"; do
    systemctl disable --now "$legacy_unit" >/dev/null 2>&1 || true
    rm -f "/etc/systemd/system/$legacy_unit"
  done
  rm -f /etc/ssh/sshd_config.d/90-rbf-backup-managed.conf
  rm -f /etc/ssh/authorized_keys/rbf-backup /etc/ssh/authorized_keys/rbf-recovery
  userdel rbf-backup >/dev/null 2>&1 || true
  userdel rbf-recovery >/dev/null 2>&1 || true
  groupdel rbf-backup-readers >/dev/null 2>&1 || true
  rm -f "$LEGACY_STATE"
  rmdir /etc/rbf-backup-server >/dev/null 2>&1 || true
  systemctl daemon-reload
  sshd -t
  systemctl reload ssh.service >/dev/null 2>&1 || systemctl reload sshd.service
fi

python3 - "$RESULT" "$ENROLLMENT_ID" "$ENVIRONMENT" "$WEBSITE_HOST" "$WEBSITE_PORT" "$USERNAME" "$STORAGE" "$WEBSITE_HOST_KEY" "$WEBSITE_FINGERPRINT" "$AGE_RECIPIENT" "$CONTROLLER_PUBLIC_KEY" <<'PY'
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
payload = {
    "schema_version": 1, "kind": "rbf-backup-enrollment-response",
    "enrollment_id": sys.argv[2], "deployment_environment": sys.argv[3],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "host": sys.argv[4], "port": int(sys.argv[5]), "username": sys.argv[6],
    "storage_directory": sys.argv[7], "remote_directory": "/exports",
    "request_directory": "/requests", "status_directory": "/status",
    "acknowledgement_directory": "/acknowledgements",
    "host_key": sys.argv[8], "host_key_fingerprint": sys.argv[9],
    "age_recipient": sys.argv[10], "controller_public_key": sys.argv[11],
    "managed_server": True, "trust_model": "backup-controller-pull-v1",
    "transport": "recovery-controller-pull-v1",
}
path.parent.mkdir(parents=True, exist_ok=True)
fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
with os.fdopen(fd, "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.chmod(temporary, 0o644)
os.replace(temporary, path)
PY
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != root ]]; then
  chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$RESULT"
fi
echo "Backup controller installed for ${ENVIRONMENT}."
echo "It connects outbound to ${WEBSITE_HOST}:${WEBSITE_PORT}; no backup-server endpoint is required."
echo "Pinned website SSH fingerprint: ${WEBSITE_FINGERPRINT}"
echo "Automatic timers are disabled. Manual fetch: rbf-recovery-tool run --target ${ENVIRONMENT}"
echo "Provisioning response: ${RESULT}"
