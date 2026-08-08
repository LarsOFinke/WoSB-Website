#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

identity=""
bundle=""
while (($#)); do
  case "$1" in
    --identity) identity="${2:-}"; shift 2 ;;
    --bundle) bundle="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --identity /path/age-key.txt --bundle /path/rbf-recovery-*.tar.gz.age"
      exit 0
      ;;
    *) die "Unknown option: $1" ;;
  esac
done

require_command age
require_command python3
identity="$(realpath "$identity")"
bundle="$(realpath "$bundle")"
[[ -f "$identity" ]] || die "age identity is missing: $identity"
[[ -f "$bundle" ]] || die "Recovery bundle is missing: $bundle"
[[ -f "${bundle}.sha256" ]] || die "Recovery checksum is missing: ${bundle}.sha256"
verify_backup_checksum "$bundle"

temporary_dir="$(mktemp -d)"
plain_bundle="$temporary_dir/recovery.tar.gz"
extracted="$temporary_dir/extracted"
cleanup() { rm -rf "$temporary_dir"; }
trap cleanup EXIT
chmod 700 "$temporary_dir"

age -d -i "$identity" -o "$plain_bundle" "$bundle"
manifest_json="$(python3 "$SCRIPT_DIR/recovery_bundle.py" extract-and-verify "$plain_bundle" "$extracted")"
python3 - "$manifest_json" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
application = payload.get("application") or {}
print("Recovery bundle is complete and cryptographically readable.")
print(f"Schema: {payload.get('schema_version')}")
print(f"Erstellt: {payload.get('created_at')}")
print(f"Anwendungsversion: {application.get('version') or 'unknown'}")
print(f"Git-Commit: {application.get('git_commit') or 'unknown'}")
print(f"Files in manifest: {len(payload.get('files') or [])}")
PY
