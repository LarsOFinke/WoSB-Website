const RESPONSE_KIND = 'rbf-backup-enrollment-response'
const REQUEST_KIND = 'rbf-backup-enrollment-request'
const SCHEMA_VERSION = 1
const ENROLLMENT_ID_PATTERN = /^[A-Za-z0-9_-]{24,128}$/
const HOST_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$/
const USERNAME_PATTERN = /^[A-Za-z0-9._-]{1,64}$/
const REMOTE_DIRECTORY_PATTERN = /^\/[A-Za-z0-9._/-]+$/
const HOST_KEY_PATTERN = /^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$/
const FINGERPRINT_PATTERN = /^SHA256:[A-Za-z0-9+/]{40,64}$/
const AGE_RECIPIENT_PATTERN = /^age1[0-9a-z]{20,}$/
const CIDR_PATTERN = /^[A-Fa-f0-9:.]+(?:\/(?:[0-9]|[1-9][0-9]|1[01][0-9]|12[0-8]))?$/
const REQUEST_FILENAME_PATTERN = /^rbf-backup-enrollment-(?:request-)?([A-Za-z0-9_-]{24,128})\.json$/
const RELEASE_VERSION_PATTERN = /^[0-9]+\.[0-9]+\.[0-9]+$/

function normalizeText(value) {
  return String(value || '').replace(/^\uFEFF/, '').trim()
}

function hasSafeRemotePath(value) {
  if (!REMOTE_DIRECTORY_PATTERN.test(value)) return false
  return !value.split('/').slice(1).some((part) => ['', '.', '..'].includes(part))
}

export function parseBackupEnrollmentResponse(value, expectedEnrollmentId = '') {
  const text = normalizeText(value)
  if (!text) return { payload: null, error: 'empty' }

  let payload
  try {
    payload = JSON.parse(text)
  } catch {
    return { payload: null, error: 'invalidJson' }
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return { payload: null, error: 'invalidObject' }
  }
  if (payload.schema_version !== SCHEMA_VERSION) {
    return { payload: null, error: 'unsupportedSchema' }
  }
  if (payload.kind === REQUEST_KIND) {
    return { payload: null, error: 'requestSelected' }
  }
  if (payload.kind !== RESPONSE_KIND) {
    return { payload: null, error: 'wrongKind' }
  }
  if (!ENROLLMENT_ID_PATTERN.test(String(payload.enrollment_id || ''))) {
    return { payload: null, error: 'invalidEnrollmentId' }
  }
  if (expectedEnrollmentId && payload.enrollment_id !== expectedEnrollmentId) {
    return { payload: null, error: 'enrollmentMismatch' }
  }
  if (!HOST_PATTERN.test(String(payload.host || ''))) {
    return { payload: null, error: 'invalidHost' }
  }
  const port = Number(payload.port)
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    return { payload: null, error: 'invalidPort' }
  }
  if (!USERNAME_PATTERN.test(String(payload.username || ''))) {
    return { payload: null, error: 'invalidUsername' }
  }
  if (!hasSafeRemotePath(String(payload.remote_directory || ''))) {
    return { payload: null, error: 'invalidRemoteDirectory' }
  }
  if (!HOST_KEY_PATTERN.test(String(payload.host_key || ''))) {
    return { payload: null, error: 'invalidHostKey' }
  }
  if (!FINGERPRINT_PATTERN.test(String(payload.host_key_fingerprint || ''))) {
    return { payload: null, error: 'invalidFingerprint' }
  }
  if (!AGE_RECIPIENT_PATTERN.test(String(payload.age_recipient || ''))) {
    return { payload: null, error: 'invalidAgeRecipient' }
  }
  if (payload.managed_server !== true) {
    return { payload: null, error: 'unmanagedServer' }
  }
  return { payload: { ...payload, port }, error: null }
}

export function normalizeBackupEnrollmentFile(value) {
  return normalizeText(value)
}


function shellQuote(value) {
  return `'${String(value).replaceAll("'", `'"'"'`)}'`
}

export function validateBackupEnrollmentSetup({
  host,
  port = 22,
  directory = '/srv/rbf-backups/wosb',
  retentionDays = 30,
  allowFrom = '',
  requestFilename = 'REQUEST.json',
  enrollmentId = '',
  releaseVersion = '',
} = {}) {
  const normalizedHost = normalizeText(host).replace(/\.$/, '')
  const normalizedPort = Number(port)
  const normalizedDirectory = normalizeText(directory).replace(/\/$/, '') || '/'
  const normalizedRetention = Number(retentionDays)
  const normalizedAllowFrom = normalizeText(allowFrom)
  const normalizedFilename = normalizeText(requestFilename)
  const normalizedEnrollmentId = normalizeText(enrollmentId)
  const normalizedReleaseVersion = normalizeText(releaseVersion)

  if (!HOST_PATTERN.test(normalizedHost)) return { values: null, error: 'invalidHost' }
  if (!Number.isInteger(normalizedPort) || normalizedPort < 1 || normalizedPort > 65535) {
    return { values: null, error: 'invalidPort' }
  }
  if (!hasSafeRemotePath(normalizedDirectory)) return { values: null, error: 'invalidDirectory' }
  if (!Number.isInteger(normalizedRetention) || normalizedRetention < 1 || normalizedRetention > 3650) {
    return { values: null, error: 'invalidRetention' }
  }
  if (normalizedAllowFrom && !CIDR_PATTERN.test(normalizedAllowFrom)) {
    return { values: null, error: 'invalidAllowFrom' }
  }
  const filenameMatch = REQUEST_FILENAME_PATTERN.exec(normalizedFilename)
  if (!filenameMatch) {
    return { values: null, error: 'invalidRequestFilename' }
  }
  const requestId = normalizedEnrollmentId || filenameMatch[1]
  if (!ENROLLMENT_ID_PATTERN.test(requestId)) {
    return { values: null, error: 'invalidEnrollmentId' }
  }
  if (!RELEASE_VERSION_PATTERN.test(normalizedReleaseVersion)) {
    return { values: null, error: 'invalidReleaseVersion' }
  }

  return {
    values: {
      host: normalizedHost,
      port: normalizedPort,
      directory: normalizedDirectory,
      retentionDays: normalizedRetention,
      allowFrom: normalizedAllowFrom,
      requestFilename: normalizedFilename,
      enrollmentId: requestId,
      responseFilename: `rbf-backup-enrollment-response-${requestId}.json`,
      releaseVersion: normalizedReleaseVersion,
    },
    error: null,
  }
}

export function buildBackupEnrollmentCommand(options = {}) {
  const result = validateBackupEnrollmentSetup(options)
  if (result.error) return { command: '', error: result.error }
  const values = result.values
  const allowFromLine = values.allowFrom
    ? `  --allow-from ${shellQuote(values.allowFrom)} \\\n`
    : ''
  const command = `( # Run setup in an isolated shell so an error cannot close this terminal.
set -e
trap 'status=$?; if [ "$status" -ne 0 ]; then echo "ERROR: Backup-server setup failed (status $status). The terminal remains open; review the message above." >&2; fi' EXIT

REQUEST="$HOME/Downloads/${values.requestFilename}"
REQUEST_ID=${shellQuote(values.enrollmentId)}
RESPONSE="$HOME/Downloads/${values.responseFilename}"
PROVISIONER="$HOME/Downloads/provision-rbf-backup-server.sh"
CHECKSUM="$PROVISIONER.sha256"
RELEASE="https://github.com/LarsOFinke/WoSB-Website/releases/download/v${values.releaseVersion}"

if [ ! -r "$REQUEST" ]; then
  REQUEST="$(python3 - "$HOME/Downloads" "$REQUEST_ID" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).expanduser().resolve()
expected = sys.argv[2]
matches = []
for candidate in sorted(root.glob("*.json")):
    try:
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size > 1024 * 1024:
            continue
        payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        continue
    if (
        isinstance(payload, dict)
        and payload.get("schema_version") == 1
        and payload.get("kind") == "rbf-backup-enrollment-request"
        and payload.get("enrollment_id") == expected
    ):
        matches.append(candidate)
if len(matches) == 1:
    print(matches[0])
elif not matches:
    print(f"ERROR: No enrollment request with ID {expected} was found in {root}.", file=sys.stderr)
    raise SystemExit(1)
else:
    names = ", ".join(path.name for path in matches)
    print(f"ERROR: Multiple enrollment requests with ID {expected} were found: {names}", file=sys.stderr)
    raise SystemExit(1)
PY
  )"
fi

test -r "$REQUEST" || {
  echo "ERROR: Enrollment request could not be read: $REQUEST"
  exit 1
}

command -v curl >/dev/null || {
  echo "ERROR: curl is required (sudo apt install curl)."
  exit 1
}
curl --fail --location --output "$PROVISIONER" "$RELEASE/provision-rbf-backup-server.sh" || exit 1
curl --fail --location --output "$CHECKSUM" "$RELEASE/provision-rbf-backup-server.sh.sha256" || exit 1
( cd "$(dirname "$PROVISIONER")" && sha256sum -c "$(basename "$CHECKSUM")" ) || exit 1

sudo bash "$PROVISIONER" \
  --request "$REQUEST" \
  --host ${shellQuote(values.host)} \
  --port ${values.port} \
  --directory ${shellQuote(values.directory)} \
  --retention-days ${values.retentionDays} \
${allowFromLine}  --result "$RESPONSE"

echo "Antwortdatei: $RESPONSE"
)`
  return { command, error: null }
}
