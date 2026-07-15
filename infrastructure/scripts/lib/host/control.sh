#!/usr/bin/env bash
set -Eeuo pipefail

# Copy a request from an API-writable inbox into a root-private work directory
# through an O_NOFOLLOW file descriptor. The host runner never parses a path it
# has not first validated and copied itself.
claim_control_request() {
  local source_path="$1" destination_path="$2" expected_uid="${3:-10001}"
  python3 - "$source_path" "$destination_path" "$expected_uid" <<'PY'
import json
import os
import stat
import sys
from pathlib import Path

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
expected_uid = int(sys.argv[3])
flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
fd = os.open(source, flags)
try:
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode):
        raise SystemExit("Control request is not a regular file.")
    if metadata.st_uid != expected_uid:
        raise SystemExit(
            f"Control request owner {metadata.st_uid} does not match expected API UID {expected_uid}."
        )
    if metadata.st_nlink != 1:
        raise SystemExit("Control request must have exactly one hard link.")
    if metadata.st_size <= 0 or metadata.st_size > 65536:
        raise SystemExit("Control request size is outside the accepted range.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise SystemExit("Control request must not be accessible by group or others.")
    chunks = []
    remaining = 65537
    while remaining > 0:
        chunk = os.read(fd, min(8192, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    data = b"".join(chunks)
finally:
    os.close(fd)

try:
    payload = json.loads(data.decode("utf-8"))
except (UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise SystemExit("Control request is not valid UTF-8 JSON.") from exc
if not isinstance(payload, dict):
    raise SystemExit("Control request JSON must be an object.")

destination.parent.mkdir(parents=True, exist_ok=True)
output_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
out = os.open(destination, output_flags, 0o600)
try:
    offset = 0
    while offset < len(data):
        offset += os.write(out, data[offset:])
    os.fsync(out)
finally:
    os.close(out)

# Removing a swapped inbox entry would only affect the unprivileged inbox. The
# trusted copy above always comes from the validated open descriptor.
try:
    os.unlink(source)
except FileNotFoundError:
    pass
PY
}
