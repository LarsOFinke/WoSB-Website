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
const SHA256_PATTERN = /^[a-f0-9]{64}$/
const DEPLOYMENT_ENVIRONMENTS = new Set(['test', 'production'])

function normalizeText(value) {
  return String(value || '').replace(/^\uFEFF/, '').trim()
}

function hasSafeRemotePath(value) {
  if (!REMOTE_DIRECTORY_PATTERN.test(value)) return false
  return !value.split('/').slice(1).some((part) => ['', '.', '..'].includes(part))
}

export function parseBackupEnrollmentResponse(value, expectedEnrollmentId = '', expectedEnvironment = '') {
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
  if (!DEPLOYMENT_ENVIRONMENTS.has(String(payload.deployment_environment || ''))
    || (expectedEnvironment && payload.deployment_environment !== expectedEnvironment)) {
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
  const environment = String(payload.deployment_environment || '')
  if (payload.username !== `rbf-backup-${environment}`
    || payload.recovery_username !== `rbf-recovery-${environment}`
    || payload.storage_directory !== `/backups/wosb/${environment}`) {
    return { payload: null, error: 'invalidUsername' }
  }
  if (!hasSafeRemotePath(String(payload.remote_directory || ''))) {
    return { payload: null, error: 'invalidRemoteDirectory' }
  }
  if (!hasSafeRemotePath(String(payload.receipt_directory || ''))
    || !hasSafeRemotePath(String(payload.recovery_directory || ''))) {
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
  if (payload.trust_model !== 'server-controlled-ingest-v1') {
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
  directory = '/backups/wosb',
  retentionDays = 30,
  allowFrom = '',
  requestFilename = 'REQUEST.json',
  enrollmentId = '',
  releaseVersion = '',
  provisionerBase64 = '',
  provisionerSha256 = '',
  ingestScriptBase64 = '',
  ingestScriptSha256 = '',
  deploymentEnvironment = '',
  requestedUsername = '',
  requestedRecoveryUsername = '',
  requestedStorageDirectory = '',
} = {}) {
  const normalizedHost = normalizeText(host).replace(/\.$/, '')
  const normalizedPort = Number(port)
  const normalizedDirectory = normalizeText(directory).replace(/\/$/, '') || '/'
  const normalizedRetention = Number(retentionDays)
  const normalizedAllowFrom = normalizeText(allowFrom)
  const normalizedFilename = normalizeText(requestFilename)
  const normalizedEnrollmentId = normalizeText(enrollmentId)
  const normalizedReleaseVersion = normalizeText(releaseVersion)
  const normalizedProvisionerBase64 = normalizeText(provisionerBase64)
  const normalizedProvisionerSha256 = normalizeText(provisionerSha256)
  const normalizedIngestScriptBase64 = normalizeText(ingestScriptBase64)
  const normalizedIngestScriptSha256 = normalizeText(ingestScriptSha256)
  const normalizedEnvironment = normalizeText(deploymentEnvironment).toLowerCase()
  const normalizedUsername = normalizeText(requestedUsername)
  const normalizedRecoveryUsername = normalizeText(requestedRecoveryUsername)
  const normalizedRequestedStorage = normalizeText(requestedStorageDirectory).replace(/\/$/, '')

  if (!HOST_PATTERN.test(normalizedHost)) return { values: null, error: 'invalidHost' }
  if (!Number.isInteger(normalizedPort) || normalizedPort < 1 || normalizedPort > 65535) {
    return { values: null, error: 'invalidPort' }
  }
  if (!hasSafeRemotePath(normalizedDirectory)) return { values: null, error: 'invalidDirectory' }
  if (!DEPLOYMENT_ENVIRONMENTS.has(normalizedEnvironment)
    || !USERNAME_PATTERN.test(normalizedUsername)
    || !USERNAME_PATTERN.test(normalizedRecoveryUsername)
    || !hasSafeRemotePath(normalizedRequestedStorage)
    || normalizedDirectory !== normalizedRequestedStorage
    || normalizedUsername !== `rbf-backup-${normalizedEnvironment}`
    || normalizedRecoveryUsername !== `rbf-recovery-${normalizedEnvironment}`
    || normalizedRequestedStorage !== `/backups/wosb/${normalizedEnvironment}`) {
    return { values: null, error: 'invalidDirectory' }
  }
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
  if (
    !normalizedProvisionerBase64
    || normalizedProvisionerBase64.length > 350000
    || !/^[A-Za-z0-9+/]+={0,2}$/.test(normalizedProvisionerBase64)
    || !SHA256_PATTERN.test(normalizedProvisionerSha256)
  ) {
    return { values: null, error: 'invalidProvisioner' }
  }
  if (
    !normalizedIngestScriptBase64
    || normalizedIngestScriptBase64.length > 350000
    || !/^[A-Za-z0-9+/]+={0,2}$/.test(normalizedIngestScriptBase64)
    || !SHA256_PATTERN.test(normalizedIngestScriptSha256)
  ) {
    return { values: null, error: 'invalidProvisioner' }
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
      provisionerSha256: normalizedProvisionerSha256,
      ingestScriptSha256: normalizedIngestScriptSha256,
      deploymentEnvironment: normalizedEnvironment,
      requestedUsername: normalizedUsername,
      requestedRecoveryUsername: normalizedRecoveryUsername,
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
DEPLOYMENT_ENVIRONMENT=${shellQuote(values.deploymentEnvironment)}
RESPONSE="$HOME/Downloads/${values.responseFilename}"
PROVISIONER="$HOME/Downloads/provision-rbf-backup-server.sh"
CHECKSUM="$PROVISIONER.sha256"
PROVISIONER_SHA=${shellQuote(values.provisionerSha256)}
INGEST="$HOME/Downloads/rbf-backup-ingest.py"
INGEST_SHA=${shellQuote(values.ingestScriptSha256)}

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

python3 - "$REQUEST" "$REQUEST_ID" "$PROVISIONER_SHA" "$PROVISIONER" "$CHECKSUM" "$INGEST_SHA" "$INGEST" <<'PY'
import base64
import binascii
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

request_path = Path(sys.argv[1])
expected_id = sys.argv[2]
expected_sha = sys.argv[3]
provisioner_path = Path(sys.argv[4])
checksum_path = Path(sys.argv[5])
expected_ingest_sha = sys.argv[6]
ingest_path = Path(sys.argv[7])
try:
    payload = json.loads(request_path.read_text(encoding="utf-8-sig"))
    encoded = str(payload.get("provisioner_base64") or "")
    provisioner = base64.b64decode(encoded, validate=True)
    encoded_ingest = str(payload.get("ingest_script_base64") or "")
    ingest_script = base64.b64decode(encoded_ingest, validate=True)
except (OSError, UnicodeError, json.JSONDecodeError, ValueError, binascii.Error) as exc:
    raise SystemExit(f"ERROR: Enrollment request has no valid embedded provisioner: {exc}") from exc
if (
    payload.get("schema_version") != 1
    or payload.get("kind") != "rbf-backup-enrollment-request"
    or payload.get("enrollment_id") != expected_id
):
    raise SystemExit("ERROR: Enrollment request does not match the active setup command.")
actual_sha = hashlib.sha256(provisioner).hexdigest()
if not provisioner or len(provisioner) > 256 * 1024 or actual_sha != expected_sha:
    raise SystemExit("ERROR: Embedded provisioner checksum verification failed.")
if payload.get("provisioner_sha256") != expected_sha:
    raise SystemExit("ERROR: Enrollment request provisioner checksum does not match the active setup command.")
actual_ingest_sha = hashlib.sha256(ingest_script).hexdigest()
if not ingest_script or len(ingest_script) > 256 * 1024 or actual_ingest_sha != expected_ingest_sha:
    raise SystemExit("ERROR: Embedded ingest service checksum verification failed.")
if payload.get("ingest_script_sha256") != expected_ingest_sha:
    raise SystemExit("ERROR: Enrollment request ingest checksum does not match the active setup command.")
provisioner_path.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(dir=provisioner_path.parent, delete=False) as handle:
    handle.write(provisioner)
    temporary = Path(handle.name)
os.chmod(temporary, 0o700)
os.replace(temporary, provisioner_path)
with tempfile.NamedTemporaryFile(
    mode="w", encoding="ascii", dir=checksum_path.parent, delete=False
) as handle:
    handle.write(f"{actual_sha}  {provisioner_path.name}\\n")
    temporary_checksum = Path(handle.name)
os.chmod(temporary_checksum, 0o600)
os.replace(temporary_checksum, checksum_path)
with tempfile.NamedTemporaryFile(dir=ingest_path.parent, delete=False) as handle:
    handle.write(ingest_script)
    temporary_ingest = Path(handle.name)
os.chmod(temporary_ingest, 0o700)
os.replace(temporary_ingest, ingest_path)
PY
( cd "$(dirname "$PROVISIONER")" && sha256sum -c "$(basename "$CHECKSUM")" ) || exit 1

sudo bash "$PROVISIONER" \
  --request "$REQUEST" \
  --ingest-script "$INGEST" \
  --user ${shellQuote(values.requestedUsername)} \
  --recovery-user ${shellQuote(values.requestedRecoveryUsername)} \
  --host ${shellQuote(values.host)} \
  --port ${values.port} \
  --directory ${shellQuote(values.directory)} \
  --retention-days ${values.retentionDays} \
${allowFromLine}  --result "$RESPONSE"

python3 - "$RESPONSE" "$REQUEST_ID" "$DEPLOYMENT_ENVIRONMENT" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
except (OSError, UnicodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"ERROR: Provisioning did not create a valid response JSON: {exc}") from exc
if (
    payload.get("schema_version") != 1
    or payload.get("kind") != "rbf-backup-enrollment-response"
    or payload.get("enrollment_id") != sys.argv[2]
    or payload.get("deployment_environment") != sys.argv[3]
):
    raise SystemExit("ERROR: Provisioning response does not match the active enrollment request.")
PY

echo "Antwortdatei: $RESPONSE"
)`
  return { command, error: null }
}
