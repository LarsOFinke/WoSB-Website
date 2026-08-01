#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "Dieses Provisioning benötigt root-Rechte." >&2; exit 1; }

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
    --skip-package-install) SKIP_PACKAGE_INSTALL=true; shift ;;
    *) echo "Unbekannte Option: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$REQUEST" && -n "$HOST" && -n "$RESULT" && -n "$RECOVERY_PUBLIC_KEY" ]] || {
  echo "--request, --host, --result und --recovery-public-key sind erforderlich." >&2
  exit 2
}
[[ "$PORT" =~ ^[0-9]+$ ]] && ((PORT >= 1 && PORT <= 65535)) || { echo "Ungültiger SSH-Port." >&2; exit 2; }
[[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]] || { echo "Ungültige Aufbewahrungsdauer." >&2; exit 2; }
[[ "$HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$ ]] || { echo "Ungültiger externer Hostname." >&2; exit 2; }
[[ "$USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || { echo "Ungültiger Upload-Benutzername." >&2; exit 2; }
[[ "$RECOVERY_USERNAME" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || { echo "Ungültiger Recovery-Benutzername." >&2; exit 2; }
[[ "$USERNAME" != "$RECOVERY_USERNAME" ]] || { echo "Upload- und Recovery-Benutzer müssen getrennt sein." >&2; exit 2; }
[[ "$DIRECTORY" =~ ^/[A-Za-z0-9._/-]+$ ]] && [[ "$DIRECTORY" != *'/../'* && "$DIRECTORY" != */.. && "$DIRECTORY" != *'/./'* ]] || {
  echo "Ungültiges Zielverzeichnis." >&2
  exit 2
}
case "$DIRECTORY" in
  /|/bin|/bin/*|/boot|/boot/*|/dev|/dev/*|/etc|/etc/*|/lib|/lib/*|/lib32|/lib32/*|/lib64|/lib64/*|/proc|/proc/*|/root|/root/*|/run|/run/*|/sbin|/sbin/*|/sys|/sys/*|/tmp|/tmp/*|/usr|/usr/*)
    echo "Das Zielverzeichnis liegt in einem geschützten Systempfad." >&2
    exit 2
    ;;
esac

python3 - "$RECOVERY_PUBLIC_KEY" <<'PY'
import re
import sys
value = sys.argv[1].strip()
if not re.fullmatch(
    r"(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?",
    value,
):
    raise SystemExit("Ungültiger lokaler Recovery-Public-Key.")
PY
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
    raise SystemExit(f"Enrollment-Anfrage nicht gefunden: {path.resolve()}") from exc
except PermissionError as exc:
    raise SystemExit(f"Keine Leseberechtigung für die Enrollment-Anfrage: {path.resolve()}") from exc
except json.JSONDecodeError as exc:
    raise SystemExit(
        f"Enrollment-Anfrage ist kein gültiges JSON (Zeile {exc.lineno}, Spalte {exc.colno}): {path.resolve()}"
    ) from exc
if payload.get("schema_version") != 1 or payload.get("kind") != "rbf-backup-enrollment-request":
    raise SystemExit("Ungültige oder nicht unterstützte Enrollment-Anfrage.")
enrollment_id = str(payload.get("enrollment_id") or "").strip()
public_key = str(payload.get("ssh_public_key") or "").strip()
requested_username = str(payload.get("requested_username") or "").strip()
requested_directory = str(payload.get("requested_directory") or "").strip().rstrip("/") or "/"
if not re.fullmatch(r"[A-Za-z0-9_-]{24,128}", enrollment_id):
    raise SystemExit("Ungültige Enrollment-ID.")
if not re.fullmatch(
    r"(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?",
    public_key,
):
    raise SystemExit("Ungültiger SSH-Public-Key.")
if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", requested_username):
    raise SystemExit("Ungültiger angeforderter SSH-Benutzer.")
if requested_directory != "/data":
    raise SystemExit("Nicht unterstützter angeforderter SFTP-Pfad; erwartet wird /data.")
print(enrollment_id)
print(public_key)
print(requested_username)
print(requested_directory)
PY
)
(( ${#request_fields[@]} == 4 )) || { echo "Enrollment-Anfrage konnte nicht vollständig gelesen werden." >&2; exit 1; }
ENROLLMENT_ID="${request_fields[0]}"
PUBLIC_KEY="${request_fields[1]}"
REQUESTED_USERNAME="${request_fields[2]}"
REQUESTED_DIRECTORY="${request_fields[3]}"
[[ "$USERNAME" == "$REQUESTED_USERNAME" ]] || {
  echo "Der CLI-Benutzer '$USERNAME' stimmt nicht mit der Enrollment-Anfrage '$REQUESTED_USERNAME' überein." >&2
  exit 1
}
[[ "$REQUESTED_DIRECTORY" == "/data" ]] || {
  echo "Die Enrollment-Anfrage erwartet einen nicht unterstützten SFTP-Pfad: $REQUESTED_DIRECTORY" >&2
  exit 1
}

if [[ "$SKIP_PACKAGE_INSTALL" != true ]] && ! command -v sshd >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y openssh-server
fi
for command_name in python3 sshd ssh-keygen useradd usermod chpasswd groupadd getent; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "Erforderliches Werkzeug fehlt: $command_name" >&2; exit 1; }
done
ssh-keygen -A
install -d -m 0755 /run/sshd
sshd -T 2>/dev/null | awk '$1 == "port" {print $2}' | grep -qx "$PORT" || {
  echo "sshd lauscht nicht auf dem angegebenen Port $PORT. Die globale Portkonfiguration wird aus Sicherheitsgründen nicht automatisch geändert." >&2
  exit 1
}

STATE_DIR="/etc/rbf-backup-server"
STATE_FILE="$STATE_DIR/${USERNAME}.json"
install -d -m 0700 -o root -g root "$STATE_DIR"
if [[ -e "$STATE_FILE" ]]; then
  [[ -f "$STATE_FILE" && ! -L "$STATE_FILE" ]] || { echo "Unsicherer Provisioning-Status: $STATE_FILE" >&2; exit 1; }
  python3 - "$STATE_FILE" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path
path = Path(sys.argv[1])
details = path.stat()
if details.st_uid != 0 or stat.S_IMODE(details.st_mode) & 0o077:
    raise SystemExit("Provisioning-Status muss root gehören und Modus 0600 besitzen.")
payload = json.loads(path.read_text(encoding="utf-8"))
if payload.get("managed_by") != "rbf-recovery-tool":
    raise SystemExit("Vorhandener Status stammt nicht vom RBF Recovery Tool.")
PY
else
  for account in "$USERNAME" "$RECOVERY_USERNAME"; do
    if id "$account" >/dev/null 2>&1; then
      echo "Der Benutzer $account existiert bereits, wurde aber nicht durch dieses Tool registriert. Abbruch zum Schutz des bestehenden Kontos." >&2
      echo "Das Recovery-Tool legt die Konten selbst an. Entferne ein nur testweise angelegtes, unbenutztes Konto bewusst vor dem erneuten Provisioning oder verwende den manuellen Web-Fallback." >&2
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
    "managed_by": "rbf-recovery-tool",
    "status": sys.argv[2],
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "enrollment_id": sys.argv[3],
    "upload_username": sys.argv[4],
    "recovery_username": sys.argv[5],
    "storage_directory": sys.argv[6],
    "data_directory": str(Path(sys.argv[6]) / "data"),
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
# by group or others. The setgid child keeps uploaded files in the read group.
CHROOT_DIRECTORY="$DIRECTORY"
DATA_DIRECTORY="$DIRECTORY/data"
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
        raise SystemExit(f"Unsicheres Chroot-Elternverzeichnis: Symlink ist nicht erlaubt: {current}")
    details = current.stat()
    if details.st_uid != 0 or details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise SystemExit(
            f"Unsicheres Chroot-Elternverzeichnis: {current} muss root gehören und darf nicht gruppen-/weltbeschreibbar sein."
        )
PY
install -d -m 2750 -o "$USERNAME" -g "$READ_GROUP" "$DATA_DIRECTORY"
chown "$USERNAME:$READ_GROUP" "$DATA_DIRECTORY"
chmod 2750 "$DATA_DIRECTORY"

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
chown root:root "$AUTHORIZED_UPLOAD" "$AUTHORIZED_RECOVERY"
chmod 0600 "$AUTHORIZED_UPLOAD" "$AUTHORIZED_RECOVERY"

SSHD_DROPIN_DIR="/etc/ssh/sshd_config.d"
SSHD_DROPIN="$SSHD_DROPIN_DIR/90-rbf-backup-managed.conf"
install -d -m 0755 -o root -g root "$SSHD_DROPIN_DIR"
SSHD_BACKUP="$(mktemp)"
SSHD_EXISTED=false
if [[ -f "$SSHD_DROPIN" && ! -L "$SSHD_DROPIN" ]]; then
  cp --preserve=mode,ownership,timestamps "$SSHD_DROPIN" "$SSHD_BACKUP"
  SSHD_EXISTED=true
elif [[ -e "$SSHD_DROPIN" ]]; then
  echo "Unsichere vorhandene SSHD-Konfiguration: $SSHD_DROPIN" >&2
  rm -f "$SSHD_BACKUP"
  exit 1
fi
cat > "$SSHD_DROPIN" <<EOF_SSHD
Match User $USERNAME
    ChrootDirectory $CHROOT_DIRECTORY
    ForceCommand internal-sftp -u 0027 -d /data
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
  echo "Die neue SSHD-Konfiguration ist ungültig und wurde zurückgerollt." >&2
  exit 1
fi
rm -f "$SSHD_BACKUP"
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now ssh.service >/dev/null 2>&1 || systemctl enable --now sshd.service >/dev/null 2>&1
  systemctl reload ssh.service >/dev/null 2>&1 || systemctl reload sshd.service >/dev/null 2>&1
fi

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
for partial in root.glob("*.part"):
    try:
        if partial.is_file() and not partial.is_symlink() and partial.stat().st_mtime < time.time() - 2 * 86400:
            partial.unlink()
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
ExecStart=$RETENTION_SCRIPT $DATA_DIRECTORY $RETENTION_DAYS
User=root
Group=root
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$DATA_DIRECTORY
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
  systemctl enable --now rbf-backup-retention.timer >/dev/null
fi

if [[ -n "$ALLOW_FROM" ]] && command -v ufw >/dev/null 2>&1 && ufw status | grep -q '^Status: active'; then
  ufw allow from "$ALLOW_FROM" to any port "$PORT" proto tcp comment 'RBF backup enrollment'
fi

HOST_KEY_FILE="/etc/ssh/ssh_host_ed25519_key.pub"
[[ -f "$HOST_KEY_FILE" ]] || { echo "Ed25519-Host-Key fehlt." >&2; exit 1; }
HOST_KEY="$(awk '{print $1" "$2}' "$HOST_KEY_FILE")"
FINGERPRINT="$(ssh-keygen -lf "$HOST_KEY_FILE" -E sha256 | awk '{print $2}')"
write_state ready

python3 - "$RESULT" "$ENROLLMENT_ID" "$HOST" "$PORT" "$USERNAME" "$RECOVERY_USERNAME" "$DIRECTORY" "$HOST_KEY" "$FINGERPRINT" "$RETENTION_DAYS" <<'PY'
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
out = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "kind": "rbf-backup-server-provisioning-result",
    "enrollment_id": sys.argv[2],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "host": sys.argv[3],
    "port": int(sys.argv[4]),
    "username": sys.argv[5],
    "recovery_username": sys.argv[6],
    "remote_directory": "/data",
    "storage_directory": sys.argv[7],
    "host_key": sys.argv[8],
    "host_key_fingerprint": sys.argv[9],
    "managed_server": True,
    "retention_days": int(sys.argv[10]),
}
out.parent.mkdir(parents=True, exist_ok=True)
fd, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=out.parent, text=True)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
os.chmod(name, 0o644)
os.replace(name, out)
PY

echo "Backup-Upload bereit: ${USERNAME}@${HOST}:${PORT}/data"
echo "Lokaler Recovery-Lesezugang: ${RECOVERY_USERNAME}@127.0.0.1:${PORT}/data (read-only)"
echo "Host-Key-Fingerprint: ${FINGERPRINT}"
echo "Provisioning-Ergebnis: ${RESULT}"
