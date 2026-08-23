const RESPONSE_KIND = 'rbf-backup-enrollment-response'
const REQUEST_KIND = 'rbf-backup-enrollment-request'
const ENROLLMENT_ID_PATTERN = /^[A-Za-z0-9_-]{24,128}$/
const HOST_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$/
const USERNAME_PATTERN = /^[A-Za-z0-9._-]{1,64}$/
const PATH_PATTERN = /^\/[A-Za-z0-9._/-]+$/
const HOST_KEY_PATTERN = /^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$/
const PUBLIC_KEY_PATTERN = /^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]{1,128})?$/
const FINGERPRINT_PATTERN = /^SHA256:[A-Za-z0-9+/]{40,64}$/
const AGE_PATTERN = /^age1[0-9a-z]{20,}$/
const SHA256_PATTERN = /^[a-f0-9]{64}$/
const VERSION_PATTERN = /^[0-9]+\.[0-9]+\.[0-9]+$/
const ENVIRONMENTS = new Set(['test', 'production'])

function text(value) {
  return String(value || '').replace(/^\uFEFF/, '').trim()
}

function safePath(value) {
  return PATH_PATTERN.test(value) && !value.split('/').slice(1).some((part) => ['', '.', '..'].includes(part))
}

export function parseBackupEnrollmentResponse(value, expectedId = '', expectedEnvironment = '') {
  let payload
  try {
    payload = JSON.parse(text(value))
  } catch {
    return { payload: null, error: 'invalidJson' }
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return { payload: null, error: 'invalidObject' }
  if (payload.schema_version !== 1) return { payload: null, error: 'unsupportedSchema' }
  if (payload.kind === REQUEST_KIND) return { payload: null, error: 'requestSelected' }
  if (payload.kind !== RESPONSE_KIND) return { payload: null, error: 'wrongKind' }
  const environment = String(payload.deployment_environment || '')
  if (!ENROLLMENT_ID_PATTERN.test(String(payload.enrollment_id || ''))) return { payload: null, error: 'invalidEnrollmentId' }
  if ((expectedId && payload.enrollment_id !== expectedId)
    || !ENVIRONMENTS.has(environment)
    || (expectedEnvironment && environment !== expectedEnvironment)) {
    return { payload: null, error: 'enrollmentMismatch' }
  }
  const port = Number(payload.port)
  if (!HOST_PATTERN.test(String(payload.host || ''))) return { payload: null, error: 'invalidHost' }
  if (!Number.isInteger(port) || port < 1 || port > 65535) return { payload: null, error: 'invalidPort' }
  if (payload.username !== `rbf-backup-controller-${environment}`
    || payload.storage_directory !== `/backups/wosb/${environment}`) {
    return { payload: null, error: 'invalidUsername' }
  }
  for (const [key, expected] of Object.entries({
    remote_directory: '/exports', request_directory: '/requests', status_directory: '/status',
    acknowledgement_directory: '/acknowledgements',
  })) {
    if (payload[key] !== expected || !safePath(String(payload[key] || ''))) {
      return { payload: null, error: 'invalidRemoteDirectory' }
    }
  }
  if (!HOST_KEY_PATTERN.test(String(payload.host_key || ''))) return { payload: null, error: 'invalidHostKey' }
  if (!FINGERPRINT_PATTERN.test(String(payload.host_key_fingerprint || ''))) return { payload: null, error: 'invalidFingerprint' }
  if (!AGE_PATTERN.test(String(payload.age_recipient || ''))) return { payload: null, error: 'invalidAgeRecipient' }
  if (!PUBLIC_KEY_PATTERN.test(String(payload.controller_public_key || ''))) return { payload: null, error: 'invalidContent' }
  if (payload.managed_server !== true
    || payload.trust_model !== 'backup-controller-pull-v1'
    || payload.transport !== 'recovery-controller-pull-v1') {
    return { payload: null, error: 'unmanagedServer' }
  }
  return { payload: { ...payload, port }, error: null }
}

export function normalizeBackupEnrollmentFile(value) {
  return text(value)
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", `'"'"'`)}'`
}

export function validateBackupEnrollmentSetup(options = {}) {
  const environment = text(options.deploymentEnvironment).toLowerCase()
  const directory = text(options.directory).replace(/\/$/, '')
  const username = text(options.requestedControllerUsername)
  const enrollmentId = text(options.enrollmentId)
  const requestFilename = text(options.requestFilename)
  const retentionDays = Number(options.retentionDays ?? 30)
  if (!ENVIRONMENTS.has(environment)
    || username !== `rbf-backup-controller-${environment}`
    || directory !== `/backups/wosb/${environment}`
    || !safePath(directory)) return { values: null, error: 'invalidDirectory' }
  if (!Number.isInteger(retentionDays) || retentionDays < 1 || retentionDays > 3650) {
    return { values: null, error: 'invalidRetention' }
  }
  if (!ENROLLMENT_ID_PATTERN.test(enrollmentId)
    || requestFilename !== `rbf-backup-enrollment-request-${enrollmentId}.json`) {
    return { values: null, error: 'invalidRequestFilename' }
  }
  if (!VERSION_PATTERN.test(text(options.releaseVersion))) return { values: null, error: 'invalidReleaseVersion' }
  const provisionerBase64 = text(options.provisionerBase64)
  const recoveryToolBase64 = text(options.recoveryToolBase64)
  if (!provisionerBase64 || provisionerBase64.length > 350000
    || !SHA256_PATTERN.test(text(options.provisionerSha256))
    || !recoveryToolBase64 || recoveryToolBase64.length > 1400000
    || !SHA256_PATTERN.test(text(options.recoveryToolSha256))) {
    return { values: null, error: 'invalidProvisioner' }
  }
  return {
    values: {
      environment, directory, username, enrollmentId, requestFilename, retentionDays,
      responseFilename: `rbf-backup-enrollment-response-${enrollmentId}.json`,
      provisionerSha256: text(options.provisionerSha256),
    },
    error: null,
  }
}

export function buildBackupEnrollmentCommand(options = {}) {
  const validated = validateBackupEnrollmentSetup(options)
  if (validated.error) return { command: '', error: validated.error }
  const value = validated.values
  const command = `( # Run setup in an isolated shell so an error cannot close this terminal.
set -e
trap 'status=$?; if [ "$status" -ne 0 ]; then echo "ERROR: Backup-controller setup failed (status $status). The terminal remains open; review the message above." >&2; fi' EXIT

REQUEST="$HOME/Downloads/${value.requestFilename}"
REQUEST_ID=${shellQuote(value.enrollmentId)}
RESPONSE="$HOME/Downloads/${value.responseFilename}"
PROVISIONER="$HOME/Downloads/provision-rbf-backup-server.sh"
CHECKSUM="$PROVISIONER.sha256"
PROVISIONER_SHA=${shellQuote(value.provisionerSha256)}

if [ ! -r "$REQUEST" ]; then
  REQUEST="$(python3 - "$HOME/Downloads" "$REQUEST_ID" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).expanduser().resolve(); expected = sys.argv[2]; matches = []
for candidate in sorted(root.glob("*.json")):
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        if (candidate.is_file() and not candidate.is_symlink() and candidate.stat().st_size <= 2 * 1024 * 1024
                and payload.get("kind") == "rbf-backup-enrollment-request"
                and payload.get("enrollment_id") == expected): matches.append(candidate)
    except (OSError, UnicodeError, json.JSONDecodeError): pass
if len(matches) != 1:
    raise SystemExit(f"ERROR: Expected exactly one enrollment request with ID {expected} in {root}; found {len(matches)}.")
print(matches[0])
PY
  )"
fi

python3 - "$REQUEST" "$REQUEST_ID" "$PROVISIONER_SHA" "$PROVISIONER" "$CHECKSUM" <<'PY'
import base64, hashlib, json, os, sys, tempfile
from pathlib import Path
request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
if request.get("enrollment_id") != sys.argv[2] or request.get("kind") != "rbf-backup-enrollment-request":
    raise SystemExit("ERROR: Enrollment request does not match this setup command.")
content = base64.b64decode(str(request.get("provisioner_base64") or ""), validate=True)
if not content or len(content) > 256 * 1024 or hashlib.sha256(content).hexdigest() != sys.argv[3]:
    raise SystemExit("ERROR: Embedded provisioner checksum verification failed.")
target = Path(sys.argv[4]); checksum = Path(sys.argv[5]); target.parent.mkdir(parents=True, exist_ok=True)
fd, temporary = tempfile.mkstemp(dir=target.parent)
with os.fdopen(fd, "wb") as handle: handle.write(content)
os.chmod(temporary, 0o700); os.replace(temporary, target)
checksum.write_text(f"{sys.argv[3]}  {target.name}\\n", encoding="ascii"); checksum.chmod(0o600)
PY
( cd "$(dirname "$PROVISIONER")" && sha256sum -c "$(basename "$CHECKSUM")" ) || exit 1
sudo bash "$PROVISIONER" --request "$REQUEST" --retention-days ${value.retentionDays} --result "$RESPONSE"
echo "Response file: $RESPONSE"
)`
  return { command, error: null }
}
