import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { join } from 'node:path'
import test from 'node:test'

import {
  buildBackupEnrollmentCommand,
  normalizeBackupEnrollmentFile,
  parseBackupEnrollmentResponse,
  validateBackupEnrollmentSetup,
} from '../src/modules/admin/domain/backupEnrollment.js'

function response(overrides = {}) {
  return {
    schema_version: 1,
    kind: 'rbf-backup-enrollment-response',
    enrollment_id: 'A'.repeat(32),
    host: '127.0.0.1',
    port: 22023,
    deployment_environment: 'production',
    username: 'rbf-backup-controller-production',
    storage_directory: '/backups/wosb/production',
    remote_directory: '/exports',
    request_directory: '/requests',
    status_directory: '/status',
    acknowledgement_directory: '/acknowledgements',
    host_key: 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=',
    host_key_fingerprint: `SHA256:${'B'.repeat(43)}`,
    age_recipient: `age1${'a'.repeat(58)}`,
    managed_server: true,
    trust_model: 'backup-controller-pull-v1',
    transport: 'recovery-controller-pull-v1',
    controller_public_key: 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIControllerKey= controller',
    ...overrides,
  }
}

function targetFields(environment = 'test') {
  return {
    enrollmentId: 'A'.repeat(32),
    deploymentEnvironment: environment,
    requestedControllerUsername: `rbf-backup-controller-${environment}`,
    requestedStorageDirectory: `/backups/wosb/${environment}`,
    directory: `/backups/wosb/${environment}`,
  }
}

test('enrollment response parser accepts the provisioner response including UTF-8 BOM', () => {
  const text = `\uFEFF${JSON.stringify(response())}\n`
  const result = parseBackupEnrollmentResponse(text, 'A'.repeat(32))
  assert.equal(result.error, null)
  assert.equal(result.payload.host, '127.0.0.1')
  assert.equal(normalizeBackupEnrollmentFile(text).startsWith('{'), true)
})

test('enrollment response parser explains mismatched or incomplete files', () => {
  assert.equal(parseBackupEnrollmentResponse('{}').error, 'unsupportedSchema')
  assert.equal(
    parseBackupEnrollmentResponse(JSON.stringify(response({ enrollment_id: 'B'.repeat(32) })), 'A'.repeat(32)).error,
    'enrollmentMismatch',
  )
  assert.equal(
    parseBackupEnrollmentResponse(JSON.stringify(response({ kind: 'rbf-backup-server-provisioning-result' }))).error,
    'wrongKind',
  )
  assert.equal(
    parseBackupEnrollmentResponse(JSON.stringify(response({ kind: 'rbf-backup-enrollment-request' }))).error,
    'requestSelected',
  )
  assert.equal(
    parseBackupEnrollmentResponse(JSON.stringify(response({ managed_server: false }))).error,
    'unmanagedServer',
  )
})


test('enrollment command builder produces a complete copy-and-paste provisioning block', () => {
  const result = buildBackupEnrollmentCommand({
    ...targetFields('production'),
    retentionDays: 30,
    requestFilename: `rbf-backup-enrollment-request-${'A'.repeat(32)}.json`,
    releaseVersion: '1.7.33',
    provisionerBase64: Buffer.from('#!/bin/sh\n').toString('base64'),
    provisionerSha256: 'b'.repeat(64),
    recoveryToolBase64: Buffer.from('recovery-tool').toString('base64'),
    recoveryToolSha256: 'c'.repeat(64),
  })
  assert.equal(result.error, null)
  assert.match(result.command, /REQUEST="\$HOME\/Downloads\/rbf-backup-enrollment-request-/)
  assert.match(result.command, /REQUEST_ID='A{32}'/)
  assert.match(result.command, /python3 - "\$HOME\/Downloads" "\$REQUEST_ID"/)
  assert.match(result.command, /RESPONSE="\$HOME\/Downloads\/rbf-backup-enrollment-response-/)
  assert.match(result.command, /provision-rbf-backup-server\.sh/)
  assert.match(result.command, /provisioner_base64/)
  assert.match(result.command, /Embedded provisioner checksum verification failed/)
  assert.doesNotMatch(result.command, /github\.com|curl --fail/)
  assert.match(result.command, /sha256sum -c/)
  assert.match(result.command, /sudo bash \"\$PROVISIONER\"/)
  assert.doesNotMatch(result.command, /BACKUP_SERVER_HOST|BACKUP_SERVER_PORT/)
  assert.match(result.command, /--retention-days 30/)
  assert.doesNotMatch(result.command, /--allow-from|--host/)
  assert.match(result.command, /--result "\$RESPONSE"/)
  assert.match(result.command, /^\( # Run setup in an isolated shell/)
})

test('a provisioning failure cannot close the interactive parent shell', () => {
  const result = buildBackupEnrollmentCommand({
    ...targetFields(),
    releaseVersion: '1.7.33',
    requestFilename: `rbf-backup-enrollment-request-${'A'.repeat(32)}.json`,
    provisionerBase64: Buffer.from('#!/bin/sh\n').toString('base64'),
    provisionerSha256: 'b'.repeat(64),
    recoveryToolBase64: Buffer.from('recovery-tool').toString('base64'),
    recoveryToolSha256: 'c'.repeat(64),
  })
  const home = mkdtempSync(join(tmpdir(), 'rbf-enrollment-command-'))
  const execution = spawnSync('bash', ['-c', `${result.command}\nprintf 'PARENT_STILL_RUNNING\\n'`], {
    env: { ...process.env, HOME: home },
    encoding: 'utf8',
  })
  assert.match(execution.stdout, /PARENT_STILL_RUNNING/)
})

test('the provisioning command runs entirely from the downloaded request', () => {
  const enrollmentId = 'A'.repeat(32)
  const provisioner = `#!/usr/bin/env bash
set -Eeuo pipefail
result=''
while (($#)); do
  if [[ "$1" == --result ]]; then result="$2"; shift 2; else shift; fi
done
printf '{"schema_version":1,"kind":"rbf-backup-enrollment-response","enrollment_id":"${enrollmentId}","deployment_environment":"test"}\\n' > "$result"
`
  const provisionerSha256 = createHash('sha256').update(provisioner).digest('hex')
  const recoveryTool = Buffer.from('recovery-tool')
  const recoveryToolSha256 = createHash('sha256').update(recoveryTool).digest('hex')
  const result = buildBackupEnrollmentCommand({
    ...targetFields(),
    releaseVersion: '1.8.1',
    requestFilename: `rbf-backup-enrollment-request-${enrollmentId}.json`,
    provisionerBase64: Buffer.from(provisioner).toString('base64'),
    provisionerSha256,
    recoveryToolBase64: recoveryTool.toString('base64'),
    recoveryToolSha256,
  })
  const home = mkdtempSync(join(tmpdir(), 'rbf-enrollment-self-contained-'))
  const downloads = join(home, 'Downloads')
  const bin = join(home, 'bin')
  mkdirSync(downloads)
  mkdirSync(bin)
  writeFileSync(join(downloads, `rbf-backup-enrollment-request-${enrollmentId}.json`), JSON.stringify({
    schema_version: 1,
    kind: 'rbf-backup-enrollment-request',
    enrollment_id: enrollmentId,
    deployment_environment: 'test',
    provisioner_base64: Buffer.from(provisioner).toString('base64'),
    provisioner_sha256: provisionerSha256,
    recovery_tool_base64: recoveryTool.toString('base64'),
    recovery_tool_sha256: recoveryToolSha256,
  }))
  writeFileSync(join(bin, 'sudo'), '#!/usr/bin/env bash\nexec "$@"\n')
  chmodSync(join(bin, 'sudo'), 0o700)

  const execution = spawnSync('bash', ['-c', result.command], {
    env: { ...process.env, HOME: home, PATH: `${bin}:${process.env.PATH}` },
    encoding: 'utf8',
  })

  assert.equal(execution.status, 0, execution.stderr)
  assert.equal(readFileSync(join(downloads, 'provision-rbf-backup-server.sh'), 'utf8'), provisioner)
  assert.match(execution.stdout, /provision-rbf-backup-server\.sh: OK/)
  assert.doesNotMatch(execution.stderr, /curl|404|GitHub/)
})

test('enrollment setup validator blocks incomplete commands before copy', () => {
  const valid = {
    ...targetFields(),
    releaseVersion: '1.7.33',
    requestFilename: `rbf-backup-enrollment-request-${'A'.repeat(32)}.json`,
    provisionerBase64: Buffer.from('#!/bin/sh\n').toString('base64'),
    provisionerSha256: 'b'.repeat(64),
    recoveryToolBase64: Buffer.from('recovery-tool').toString('base64'),
    recoveryToolSha256: 'c'.repeat(64),
  }
  assert.equal(validateBackupEnrollmentSetup(valid).error, null)
  assert.equal(validateBackupEnrollmentSetup({ ...valid, directory: '../backups' }).error, 'invalidDirectory')
  assert.equal(validateBackupEnrollmentSetup({ ...valid, retentionDays: 0 }).error, 'invalidRetention')
  assert.equal(validateBackupEnrollmentSetup({ ...valid, releaseVersion: 'latest' }).error, 'invalidReleaseVersion')
  assert.equal(validateBackupEnrollmentSetup({ ...valid, provisionerSha256: 'short' }).error, 'invalidProvisioner')
})
