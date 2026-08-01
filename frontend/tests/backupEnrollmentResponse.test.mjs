import assert from 'node:assert/strict'
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
    host: '192.168.2.107',
    port: 22,
    username: 'rbf-backup',
    remote_directory: '/data',
    host_key: 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=',
    host_key_fingerprint: `SHA256:${'B'.repeat(43)}`,
    age_recipient: `age1${'a'.repeat(58)}`,
    managed_server: true,
    ...overrides,
  }
}

test('enrollment response parser accepts the Recovery Tool response including UTF-8 BOM', () => {
  const text = `\uFEFF${JSON.stringify(response())}\n`
  const result = parseBackupEnrollmentResponse(text, 'A'.repeat(32))
  assert.equal(result.error, null)
  assert.equal(result.payload.host, '192.168.2.107')
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
    parseBackupEnrollmentResponse(JSON.stringify(response({ managed_server: false }))).error,
    'unmanagedServer',
  )
})


test('enrollment command builder produces a complete copy-and-paste provisioning block', () => {
  const result = buildBackupEnrollmentCommand({
    host: '192.168.2.107',
    port: 22,
    directory: '/srv/rbf-backups/wosb',
    retentionDays: 30,
    allowFrom: '192.168.2.36/32',
    requestFilename: `rbf-backup-enrollment-${'A'.repeat(32)}.json`,
  })
  assert.equal(result.error, null)
  assert.match(result.command, /REQUEST="\$HOME\/Downloads\/rbf-backup-enrollment-/)
  assert.match(result.command, /command -v rbf-recovery-tool/)
  assert.match(result.command, /rbf-recovery-tool server provision/)
  assert.match(result.command, /--host '192\.168\.2\.107'/)
  assert.match(result.command, /--directory '\/srv\/rbf-backups\/wosb'/)
  assert.match(result.command, /--allow-from '192\.168\.2\.36\/32'/)
  assert.match(result.command, /--output "\$RESPONSE"/)
})

test('enrollment setup validator blocks incomplete commands before copy', () => {
  assert.equal(validateBackupEnrollmentSetup({ host: '' }).error, 'invalidHost')
  assert.equal(validateBackupEnrollmentSetup({ host: 'backup.local', port: 70000 }).error, 'invalidPort')
  assert.equal(validateBackupEnrollmentSetup({ host: 'backup.local', directory: '../backups' }).error, 'invalidDirectory')
  assert.equal(validateBackupEnrollmentSetup({ host: 'backup.local', retentionDays: 0 }).error, 'invalidRetention')
})
