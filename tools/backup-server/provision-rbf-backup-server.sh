#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "This provisioning requires root privileges." >&2; exit 1; }

REQUEST=""
HOST=""
PORT=22
USERNAME="rbf-backup"
RECOVERY_USERNAME="rbf-recovery"
RECOVERY_PUBLIC_KEY=""
DIRECTORY="/srv/rbf-backups/wosb"
RESULT=""
ALLOW_FROM=""
SKIP_PACKAGE_INSTALL=false
RETENTION_DAYS=30
INGEST_SCRIPT=""

while (($#)); do
  case "$1" in
    --request) REQUEST="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --user) USERNAME="$2"; shift 2 ;;
    --recovery-user) RECOVERY_USERNAME="$2"; shift 2 ;;
    --recovery-public-key) RECOVERY_PUBLIC_KEY="$2"; shift 2 ;;
    --directory) DIRECTORY="$2"; shift 2 ;;
    --result) RESULT="$2"; shift 2 ;;
    --allow-from) ALLOW_FROM="$2"; shift 2 ;;
    --retention-days) RETENTION_DAYS="$2"; shift 2 ;;
    --ingest-script) INGEST_SCRIPT="$2"; shift 2 ;;
    --skip-package-install) SKIP_PACKAGE_INSTALL=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$REQUEST" && -f "$INGEST_SCRIPT" && ! -L "$INGEST_SCRIPT" && -n "$HOST" && -n "$RESULT" ]] || {
  echo "--request, --ingest-script, --host, and --result are required." >&2
  exit 2
}
[[ "$PORT" =~ ^[0-9]+$ ]] && ((PORT >= 1 && PORT <= 65535)) || { echo "Invalid SSH port." >&2; exit 2; }
[[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid retention period." >&2; exit 2; }
[[ "$HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$ ]] || { echo "Invalid external hostname." >&2; exit 2; }
[[ "$USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || { echo "Invalid upload username." >&2; exit 2; }
[[ "$RECOVERY_USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || { echo "Invalid recovery username." >&2; exit 2; }
[[ "$USERNAME" != "$RECOVERY_USERNAME" ]] || { echo "Upload and recovery users must be separate." >&2; exit 2; }
[[ "$DIRECTORY" =~ ^/[A-Za-z0-9._/-]+$ ]] && [[ "$DIRECTORY" != *'/../'* && "$DIRECTORY" != */.. && "$DIRECTORY" != *'/./'* ]] || {
  echo "Invalid target directory." >&2
  exit 2
}
case "$DIRECTORY" in
  /|/bin|/bin/*|/boot|/boot/*|/dev|/dev/*|/etc|/etc/*|/lib|/lib/*|/lib32|/lib32/*|/lib64|/lib64/*|/proc|/proc/*|/root|/root/*|/run|/run/*|/sbin|/sbin/*|/sys|/sys/*|/tmp|/tmp/*|/usr|/usr/*)
    echo "The target directory is located in a protected system path." >&2
    exit 2
    ;;
esac

if [[ -n "$ALLOW_FROM" ]]; then
  python3 - "$ALLOW_FROM" <<'PY'
import ipaddress
import sys
ipaddress.ip_network(sys.argv[1], strict=False)
PY
fi

readarray -t request_fields < <(python3 - "$REQUEST" <<'PY'
import json
import re
import sys
from pathlib import Path
path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
except FileNotFoundError as exc:
    raise SystemExit(f"Enrollment request not found: {path.resolve()}") from exc
except PermissionError as exc:
    raise SystemExit(f"No read permission for the enrollment request: {path.resolve()}") from exc
except json.JSONDecodeError as exc:
    raise SystemExit(
        f"Enrollment request is not valid JSON (line {exc.lineno}, column {exc.colno}): {path.resolve()}"
    ) from exc
if payload.get("schema_version") != 1 or payload.get("kind") != "rbf-backup-enrollment-request":
    raise SystemExit("Invalid or unsupported enrollment request.")
enrollment_id = str(payload.get("enrollment_id") or "").strip()
public_key = str(payload.get("ssh_public_key") or "").strip()
requested_username = str(payload.get("requested_username") or "").strip()
requested_directory = str(payload.get("requested_directory") or "").strip().rstrip("/") or "/"
ingest_script_sha256 = str(payload.get("ingest_script_sha256") or "").strip()
if not re.fullmatch(r"[A-Za-z0-9_-]{24,128}", enrollment_id):
    raise SystemExit("Invalid enrollment ID.")
if not re.fullmatch(
    r"(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?",
    public_key,
):
    raise SystemExit("Invalid SSH public key.")
if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", requested_username):
    raise SystemExit("Invalid requested SSH user.")
if requested_directory != "/incoming":
    raise SystemExit("Unsupported requested SFTP path; expected /incoming.")
if not re.fullmatch(r"[a-f0-9]{64}", ingest_script_sha256):
    raise SystemExit("Invalid ingest script checksum.")
print(enrollment_id)
print(public_key)
print(requested_username)
print(requested_directory)
print(ingest_script_sha256)
PY
)
(( ${#request_fields[@]} == 5 )) || { echo "Enrollment request could not be read completely." >&2; exit 1; }
ENROLLMENT_ID="${request_fields[0]}"
PUBLIC_KEY="${request_fields[1]}"
REQUESTED_USERNAME="${request_fields[2]}"
REQUESTED_DIRECTORY="${request_fields[3]}"
INGEST_SCRIPT_SHA256="${request_fields[4]}"
[[ "$USERNAME" == "$REQUESTED_USERNAME" ]] || {
  echo "The CLI user '$USERNAME' does not match the enrollment request '$REQUESTED_USERNAME'." >&2
  exit 1
}
[[ "$REQUESTED_DIRECTORY" == "/incoming" ]] || {
  echo "The enrollment request expects an unsupported SFTP path: $REQUESTED_DIRECTORY" >&2
  exit 1
}
[[ "$(sha256sum "$INGEST_SCRIPT" | awk '{print $1}')" == "$INGEST_SCRIPT_SHA256" ]] || {
  echo "The ingest script does not match the enrollment request checksum." >&2
  exit 1
}

if [[ "$SKIP_PACKAGE_INSTALL" != true ]] && { ! command -v sshd >/dev/null 2>&1 || ! command -v age-keygen >/dev/null 2>&1; }; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y openssh-server age
fi
for command_name in python3 sshd ssh-keygen age-keygen sha256sum stat useradd usermod chpasswd groupadd getent; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "Required tool is missing: $command_name" >&2; exit 1; }
done
ssh-keygen -A
install -d -m 0755 /run/sshd
sshd -T 2>/dev/null | awk '$1 == "port" {print $2}' | grep -qx "$PORT" || {
  echo "sshd is not listening on the specified port $PORT. The global port configuration is not changed automatically for safety reasons." >&2
  exit 1
}

OPERATOR_USER="${SUDO_USER:-root}"
OPERATOR_HOME="$(getent passwd "$OPERATOR_USER" | cut -d: -f6)"
[[ -n "$OPERATOR_HOME" && "$OPERATOR_HOME" == /* ]] || { echo "Operator home could not be determined." >&2; exit 1; }
STATE_DIR="/etc/rbf-backup-server"
STATE_FILE="$STATE_DIR/${USERNAME}.json"
EXISTING_MANAGED=false
install -d -m 0700 -o root -g root "$STATE_DIR"
if [[ -e "$STATE_FILE" ]]; then
  [[ -f "$STATE_FILE" && ! -L "$STATE_FILE" ]] || { echo "Unsafe provisioning state: $STATE_FILE" >&2; exit 1; }
  python3 - "$STATE_FILE" "$USERNAME" "$RECOVERY_USERNAME" "$DIRECTORY" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path
path = Path(sys.argv[1])
details = path.stat()
if details.st_uid != 0 or stat.S_IMODE(details.st_mode) & 0o077:
    raise SystemExit("Provisioning state must be owned by root with no group or world access.")
payload = json.loads(path.read_text(encoding="utf-8"))
expected = {
    "managed_by": "rbf-backup-server-provisioner",
    "upload_username": sys.argv[2],
    "recovery_username": sys.argv[3],
    "storage_directory": sys.argv[4],
}
for key, value in expected.items():
    if payload.get(key) != value:
        raise SystemExit(f"Existing managed state does not match {key}.")
PY
  EXISTING_MANAGED=true
fi

RECOVERY_DIR="${RBF_RECOVERY_DIRECTORY:-$OPERATOR_HOME/RBF-Recovery}"
install -d -m 0700 "$RECOVERY_DIR"
if [[ -z "$RECOVERY_PUBLIC_KEY" ]]; then
  RECOVERY_KEY="$RECOVERY_DIR/rbf-recovery-readonly-ed25519"
  if [[ -e "$RECOVERY_KEY" || -e "$RECOVERY_KEY.pub" ]]; then
    [[ "$EXISTING_MANAGED" == true && -f "$RECOVERY_KEY" && ! -L "$RECOVERY_KEY" \
        && -f "$RECOVERY_KEY.pub" && ! -L "$RECOVERY_KEY.pub" ]] || {
      echo "Existing recovery key material is incomplete or is not tied to this managed server." >&2
      exit 1
    }
  else
    ssh-keygen -q -t ed25519 -N '' -C 'rbf-recovery-readonly' -f "$RECOVERY_KEY"
  fi
  RECOVERY_PUBLIC_KEY="$(cat "$RECOVERY_KEY.pub")"
fi
python3 - "$RECOVERY_PUBLIC_KEY" <<'PY'
import re,sys
value=sys.argv[1].strip()
if not re.fullmatch(r"(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?",value):
    raise SystemExit("Invalid recovery public key.")
PY
AGE_IDENTITY="$RECOVERY_DIR/rbf-recovery-identity.txt"
if [[ -e "$AGE_IDENTITY" ]]; then
  [[ "$EXISTING_MANAGED" == true && -f "$AGE_IDENTITY" && ! -L "$AGE_IDENTITY" ]] || {
    echo "Existing age identity is not tied to this managed server." >&2
    exit 1
  }
else
  age-keygen -o "$AGE_IDENTITY" >/dev/null
fi
AGE_RECIPIENT="$(age-keygen -y "$AGE_IDENTITY")"
chmod 0600 "$AGE_IDENTITY" "${RECOVERY_KEY:-$AGE_IDENTITY}" 2>/dev/null || true
chown -R "$OPERATOR_USER":"$(id -gn "$OPERATOR_USER")" "$RECOVERY_DIR"

if [[ "$EXISTING_MANAGED" != true ]]; then
  for account in "$USERNAME" "$RECOVERY_USERNAME"; do
    if id "$account" >/dev/null 2>&1; then
      echo "User $account already exists but was not registered by this tool. Aborting to protect the existing account." >&2
      echo "The recovery tool creates the accounts itself. Deliberately remove an unused account created only for testing before provisioning again, or use the manual web fallback." >&2
      exit 1
    fi
  done
fi

write_state() {
  local status="$1"
  python3 - "$STATE_FILE" "$status" "$ENROLLMENT_ID" "$USERNAME" "$RECOVERY_USERNAME" "$DIRECTORY" "$RETENTION_DAYS" <<'PY'
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
out = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "managed_by": "rbf-backup-server-provisioner",
    "status": sys.argv[2],
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "enrollment_id": sys.argv[3],
    "upload_username": sys.argv[4],
    "recovery_username": sys.argv[5],
    "storage_directory": sys.argv[6],
    "data_directory": str(Path(sys.argv[6]) / "data"),
    "incoming_directory": str(Path(sys.argv[6]) / "incoming"),
    "receipt_directory": str(Path(sys.argv[6]) / "receipts"),
    "trust_model": "server-controlled-ingest-v1",
    "retention_days": int(sys.argv[7]),
}
fd, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=out.parent, text=True)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
os.chmod(name, 0o600)
os.replace(name, out)
PY
}
write_state provisioning

READ_GROUP="rbf-backup-readers"
getent group "$READ_GROUP" >/dev/null 2>&1 || groupadd --system "$READ_GROUP"
if ! id "$USERNAME" >/dev/null 2>&1; then
  useradd --no-create-home --home-dir /data --shell /usr/sbin/nologin --user-group "$USERNAME"
else
  usermod --home /data --shell /usr/sbin/nologin "$USERNAME"
fi
if ! id "$RECOVERY_USERNAME" >/dev/null 2>&1; then
  useradd --no-create-home --home-dir /data --shell /usr/sbin/nologin --user-group "$RECOVERY_USERNAME"
else
  usermod --home /data --shell /usr/sbin/nologin "$RECOVERY_USERNAME"
fi
usermod -a -G "$READ_GROUP" "$RECOVERY_USERNAME"

# OpenSSH rejects locked accounts before public-key authentication. Give both
# key-only SFTP accounts an unknown high-entropy password instead. Password and
# keyboard-interactive SSH authentication remain disabled in the Match blocks,
# and both accounts keep /usr/sbin/nologin as their shell.
set_unknown_password() {
  local account="$1"
  python3 - "$account" <<'PY' | chpasswd
import secrets
import sys
print(f"{sys.argv[1]}:{secrets.token_urlsafe(48)}")
PY
}
set_unknown_password "$USERNAME"
set_unknown_password "$RECOVERY_USERNAME"

# OpenSSH requires every chroot path component to be root-owned and not writable
# by group or others. The website can write only to incoming, can read only
# server-issued receipts, and cannot traverse the protected committed store.
CHROOT_DIRECTORY="$DIRECTORY"
DATA_DIRECTORY="$DIRECTORY/data"
INCOMING_DIRECTORY="$DIRECTORY/incoming"
RECEIPT_DIRECTORY="$DIRECTORY/receipts"
install -d -m 0755 -o root -g root "$CHROOT_DIRECTORY"
python3 - "$CHROOT_DIRECTORY" <<'PY'
from pathlib import Path
import stat
import sys
requested = Path(sys.argv[1])
current = Path("/")
for part in requested.parts[1:]:
    current /= part
    if current.is_symlink():
        raise SystemExit(f"Unsafe chroot parent directory: symlinks are not allowed: {current}")
    details = current.stat()
    if details.st_uid != 0 or details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise SystemExit(
            f"Unsafe chroot parent directory: {current} must be owned by root and must not be group/world-writable."
        )
PY
if [[ -d "$DATA_DIRECTORY" && ! -L "$DATA_DIRECTORY" && "$(stat -c %u "$DATA_DIRECTORY")" != 0 ]]; then
  python3 - "$DATA_DIRECTORY" "$(getent group "$READ_GROUP" | cut -d: -f3)" <<'PY'
from pathlib import Path
import os
import shutil
import sys
import tempfile

source = Path(sys.argv[1])
group_id = int(sys.argv[2])
stage = Path(tempfile.mkdtemp(prefix=".data-protected-", dir=source.parent))
legacy = source.with_name(f".data-untrusted-{os.getpid()}")
try:
    for candidate in source.iterdir():
        details = candidate.lstat()
        if not candidate.is_file() or candidate.is_symlink() or details.st_nlink != 1:
            raise RuntimeError(f"Cannot migrate unsafe legacy backup entry: {candidate.name}")
        target = stage / candidate.name
        shutil.copyfile(candidate, target)
        os.chown(target, 0, group_id)
        os.chmod(target, 0o640)
    os.chown(stage, 0, group_id)
    os.chmod(stage, 0o750)
    os.rename(source, legacy)
    try:
        os.rename(stage, source)
    except Exception:
        os.rename(legacy, source)
        raise
    shutil.rmtree(legacy)
except Exception:
    shutil.rmtree(stage, ignore_errors=True)
    raise
PY
fi
install -d -m 0750 -o root -g "$READ_GROUP" "$DATA_DIRECTORY"
chown root:"$READ_GROUP" "$DATA_DIRECTORY"
chmod 0750 "$DATA_DIRECTORY"
find "$DATA_DIRECTORY" -mindepth 1 -maxdepth 1 -type f -exec chown root:"$READ_GROUP" {} +
find "$DATA_DIRECTORY" -mindepth 1 -maxdepth 1 -type f -exec chmod 0640 {} +
install -d -m 0700 -o "$USERNAME" -g "$USERNAME" "$INCOMING_DIRECTORY"
chown "$USERNAME:$USERNAME" "$INCOMING_DIRECTORY"
chmod 0700 "$INCOMING_DIRECTORY"
install -d -m 0550 -o root -g "$USERNAME" "$RECEIPT_DIRECTORY"
chown root:"$USERNAME" "$RECEIPT_DIRECTORY"
chmod 0550 "$RECEIPT_DIRECTORY"

AUTH_ROOT="/etc/ssh/authorized_keys"
install -d -m 0755 -o root -g root "$AUTH_ROOT"
AUTHORIZED_UPLOAD="$AUTH_ROOT/$USERNAME"
AUTHORIZED_RECOVERY="$AUTH_ROOT/$RECOVERY_USERNAME"
if [[ -n "$ALLOW_FROM" ]]; then
  printf 'restrict,from="%s" %s\n' "$ALLOW_FROM" "$PUBLIC_KEY" > "$AUTHORIZED_UPLOAD"
else
  printf 'restrict %s\n' "$PUBLIC_KEY" > "$AUTHORIZED_UPLOAD"
fi
printf 'restrict,from="127.0.0.1,::1" %s\n' "$RECOVERY_PUBLIC_KEY" > "$AUTHORIZED_RECOVERY"
chown root:"$USERNAME" "$AUTHORIZED_UPLOAD"
chown root:"$RECOVERY_USERNAME" "$AUTHORIZED_RECOVERY"
chmod 0640 "$AUTHORIZED_UPLOAD" "$AUTHORIZED_RECOVERY"

SSHD_DROPIN_DIR="/etc/ssh/sshd_config.d"
SSHD_DROPIN="$SSHD_DROPIN_DIR/90-rbf-backup-managed.conf"
install -d -m 0755 -o root -g root "$SSHD_DROPIN_DIR"
SSHD_BACKUP="$(mktemp)"
SSHD_EXISTED=false
if [[ -f "$SSHD_DROPIN" && ! -L "$SSHD_DROPIN" ]]; then
  cp --preserve=mode,ownership,timestamps "$SSHD_DROPIN" "$SSHD_BACKUP"
  SSHD_EXISTED=true
elif [[ -e "$SSHD_DROPIN" ]]; then
  echo "Unsafe existing SSHD configuration: $SSHD_DROPIN" >&2
  rm -f "$SSHD_BACKUP"
  exit 1
fi
cat > "$SSHD_DROPIN" <<EOF_SSHD
Match User $USERNAME
    ChrootDirectory $CHROOT_DIRECTORY
    ForceCommand internal-sftp -u 0077 -d /incoming
    AuthorizedKeysFile $AUTH_ROOT/%u
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PubkeyAuthentication yes
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
    PermitTTY no

Match User $RECOVERY_USERNAME
    ChrootDirectory $CHROOT_DIRECTORY
    ForceCommand internal-sftp -R -d /data
    AuthorizedKeysFile $AUTH_ROOT/%u
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PubkeyAuthentication yes
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
    PermitTTY no
EOF_SSHD
chmod 0644 "$SSHD_DROPIN"
chown root:root "$SSHD_DROPIN"
if ! sshd -t; then
  if [[ "$SSHD_EXISTED" == true ]]; then
    install -m 0644 -o root -g root "$SSHD_BACKUP" "$SSHD_DROPIN"
  else
    rm -f "$SSHD_DROPIN"
  fi
  rm -f "$SSHD_BACKUP"
  sshd -t >/dev/null 2>&1 || true
  echo "The new SSHD configuration is invalid and was rolled back." >&2
  exit 1
fi
rm -f "$SSHD_BACKUP"
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now ssh.service >/dev/null 2>&1 || systemctl enable --now sshd.service >/dev/null 2>&1
  systemctl reload ssh.service >/dev/null 2>&1 || systemctl reload sshd.service >/dev/null 2>&1
fi

INGEST_PROCESSOR="/usr/local/sbin/rbf-backup-ingest"
python3 -m py_compile "$INGEST_SCRIPT"
install -m 0755 -o root -g root "$INGEST_SCRIPT" "$INGEST_PROCESSOR"
READ_GROUP_ID="$(getent group "$READ_GROUP" | cut -d: -f3)"
UPLOAD_GROUP_ID="$(getent group "$USERNAME" | cut -d: -f3)"
cat > /etc/systemd/system/rbf-backup-ingest.service <<EOF_INGEST_SERVICE
[Unit]
Description=Validate and commit RBF website backup submissions
After=local-fs.target

[Service]
Type=oneshot
ExecStart=$INGEST_PROCESSOR $INCOMING_DIRECTORY $DATA_DIRECTORY $RECEIPT_DIRECTORY --read-group-id $READ_GROUP_ID --upload-group-id $UPLOAD_GROUP_ID
User=root
Group=root
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$INCOMING_DIRECTORY $DATA_DIRECTORY $RECEIPT_DIRECTORY
ProtectHome=true
MemoryMax=256M
CPUQuota=50%
TasksMax=32
EOF_INGEST_SERVICE
cat > /etc/systemd/system/rbf-backup-ingest.path <<EOF_INGEST_PATH
[Unit]
Description=Watch for completed RBF website backup submissions

[Path]
PathChanged=$INCOMING_DIRECTORY
Unit=rbf-backup-ingest.service

[Install]
WantedBy=multi-user.target
EOF_INGEST_PATH
cat > /etc/systemd/system/rbf-backup-ingest.timer <<'EOF_INGEST_TIMER'
[Unit]
Description=Fallback scan for RBF website backup submissions

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
AccuracySec=10s

[Install]
WantedBy=timers.target
EOF_INGEST_TIMER

RETENTION_SCRIPT="/usr/local/sbin/rbf-backup-retention"
cat > "$RETENTION_SCRIPT" <<'RETENTION'
#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
import time

root = Path(sys.argv[1]).resolve()
days = int(sys.argv[2])
receipts = Path(sys.argv[3]).resolve()
cutoff = time.time() - days * 86400
for manifest in sorted(root.glob("rbf-backup-set-*.json")):
    try:
        if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_mtime >= cutoff:
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or payload.get("committed") is not True:
            continue
        names = {manifest.name, manifest.name + ".sha256"}
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, dict):
            for record in artifacts.values():
                if not isinstance(record, dict):
                    continue
                candidates = [record]
                metadata = record.get("restore_metadata")
                if isinstance(metadata, dict):
                    candidates.append(metadata)
                for candidate_record in candidates:
                    name = str(candidate_record.get("filename") or "")
                    if name and Path(name).name == name:
                        names.update({name, name + ".sha256"})
        for name in names:
            candidate = (root / name).resolve()
            if candidate.parent == root and candidate.is_file() and not candidate.is_symlink():
                candidate.unlink()
    except (OSError, ValueError, json.JSONDecodeError):
        continue
for receipt in receipts.glob("rbf-backup-set-*.json.receipt.json"):
    try:
        if receipt.is_file() and not receipt.is_symlink() and receipt.stat().st_mtime < cutoff:
            receipt.unlink()
    except OSError:
        pass
RETENTION
chmod 0755 "$RETENTION_SCRIPT"
chown root:root "$RETENTION_SCRIPT"
cat > /etc/systemd/system/rbf-backup-retention.service <<EOF_SERVICE
[Unit]
Description=RBF backup-server retention cleanup
After=local-fs.target

[Service]
Type=oneshot
ExecStart=$RETENTION_SCRIPT $DATA_DIRECTORY $RETENTION_DAYS $RECEIPT_DIRECTORY
User=root
Group=root
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$DATA_DIRECTORY $RECEIPT_DIRECTORY
ProtectHome=true
EOF_SERVICE
cat > /etc/systemd/system/rbf-backup-retention.timer <<'EOF_TIMER'
[Unit]
Description=Daily RBF backup-server retention cleanup

[Timer]
OnCalendar=*-*-* 04:30:00
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target
EOF_TIMER
if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload
  systemctl enable --now rbf-backup-ingest.path rbf-backup-ingest.timer >/dev/null
  systemctl start rbf-backup-ingest.service
  systemctl enable --now rbf-backup-retention.timer >/dev/null
fi

if [[ -n "$ALLOW_FROM" ]] && command -v ufw >/dev/null 2>&1 && ufw status | grep -q '^Status: active'; then
  ufw allow from "$ALLOW_FROM" to any port "$PORT" proto tcp comment 'RBF backup enrollment'
fi

HOST_KEY_FILE="/etc/ssh/ssh_host_ed25519_key.pub"
[[ -f "$HOST_KEY_FILE" ]] || { echo "Ed25519 host key is missing." >&2; exit 1; }
HOST_KEY="$(awk '{print $1" "$2}' "$HOST_KEY_FILE")"
FINGERPRINT="$(ssh-keygen -lf "$HOST_KEY_FILE" -E sha256 | awk '{print $2}')"
write_state ready

python3 - "$RESULT" "$ENROLLMENT_ID" "$HOST" "$PORT" "$USERNAME" "$RECOVERY_USERNAME" "$DIRECTORY" "$HOST_KEY" "$FINGERPRINT" "$RETENTION_DAYS" "$AGE_RECIPIENT" <<'PY'
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
out = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "kind": "rbf-backup-enrollment-response",
    "enrollment_id": sys.argv[2],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "host": sys.argv[3],
    "port": int(sys.argv[4]),
    "username": sys.argv[5],
    "recovery_username": sys.argv[6],
    "remote_directory": "/incoming",
    "receipt_directory": "/receipts",
    "recovery_directory": "/data",
    "storage_directory": sys.argv[7],
    "host_key": sys.argv[8],
    "host_key_fingerprint": sys.argv[9],
    "managed_server": True,
    "trust_model": "server-controlled-ingest-v1",
    "retention_days": int(sys.argv[10]),
    "age_recipient": sys.argv[11],
}
out.parent.mkdir(parents=True, exist_ok=True)
fd, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=out.parent, text=True)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
os.chmod(name, 0o644)
os.replace(name, out)
PY

echo "Website-server submission ready: ${USERNAME}@${HOST}:${PORT}/incoming"
echo "Website-server receipt access: ${USERNAME}@${HOST}:${PORT}/receipts (read-only by filesystem ownership)"
echo "Local recovery read access: ${RECOVERY_USERNAME}@127.0.0.1:${PORT}/data (read-only)"
echo "Host-Key-Fingerprint: ${FINGERPRINT}"
echo "Provisioning-Ergebnis: ${RESULT}"
echo "Private recovery files: ${RECOVERY_DIR} (also keep an encrypted offline backup)"
