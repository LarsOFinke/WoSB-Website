import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('database backup administration is isolated in an admin-only subpage', async () => {
  const [routes, navigation, page, composable] = await Promise.all([
    read('src/modules/admin/routes.js'),
    read('src/modules/admin/domain/staffNavigation.js'),
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
    read('src/modules/admin/composables/useDatabaseBackupsPage.js'),
  ])

  assert.match(routes, /path: '\/admin\/database-backups'/)
  assert.match(routes, /requiresAdmin: true/)
  assert.match(navigation, /key: 'backups'/)
  assert.match(page, /useDatabaseBackupsPage/)
  assert.doesNotMatch(page, /modules\/admin\/api\/admin/)
  assert.match(composable, /runApplicationBackup/)
  assert.match(composable, /window\.confirm\(t\('admin\.backups\.confirmRun'\)\)/)
  assert.match(page, /connectionReady/)
  assert.match(page, /prepareEnrollment/)
  assert.match(page, /downloadEnrollmentRequest/)
  assert.match(page, /loadEnrollmentResponse/)
  assert.match(composable, /useBackupEnrollment/)
  assert.match(composable, /hasHostApproval/)
  assert.doesNotMatch(page, /private_key|local\/restore|arm-admin-restore/)
  assert.doesNotMatch(composable, /private_key|restoreLocal|configureBackup|discoverBackup/)
})

test('backup connection API exposes no browser-side secret persistence', async () => {
  const [api, page, messages] = await Promise.all([
    read('src/modules/admin/api/admin.js'),
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
    read('src/locales/messages/backupManagement.js'),
  ])

  assert.match(api, /get\('\/admin\/backups\/status'\)/)
  assert.match(api, /post\('\/admin\/backups\/run'/)
  assert.doesNotMatch(page, /localStorage|sessionStorage/)
  for (const locale of ['en', 'de', 'fr', 'es', 'pt', 'ru', 'cn']) {
    assert.match(messages, new RegExp(`\\b${locale}: \\{`))
  }
  assert.match(messages, /recovery: 'Encrypted disaster-recovery bundle'/)
  assert.match(messages, /recovery: 'Verschlüsseltes Disaster-Recovery-Bundle'/)
})

test('backup progress polling backs off through the planned consistency pause', async () => {
  const [composable, polling, page] = await Promise.all([
    read('src/modules/admin/composables/useDatabaseBackupsPage.js'),
    read('src/modules/admin/domain/backupStatusPolling.js'),
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
  ])

  assert.match(composable, /statusPollFailures\.value \+= 1/)
  assert.match(composable, /statusPollFailures\.value = 0/)
  assert.match(composable, /backupStatusPollDelay/)
  assert.match(composable, /status\.value\.progress_percent/)
  assert.doesNotMatch(composable, /\}, 2500\)/)
  assert.match(polling, /BACKUP_STATUS_MAX_BACKOFF_MS = 30000/)
  assert.match(polling, /normalizedMessage\.includes\('preparing'\)/)
  assert.match(page, /statusPollingDelayed/)
})

test('the browser surface does not expose recovery transfers or restore controls', async () => {
  const page = await read('src/modules/admin/pages/DatabaseBackupsPage.vue')
  assert.doesNotMatch(page, /local\/restore|restoreDatabase|restoreFiles|type="password"|approval_token/)
  assert.match(page, /runBackup/)
  assert.match(page, /status\.artifacts/)
})

test('guided enrollment uses the host capability and keeps recovery tooling optional', async () => {
  const [page, composable, pageComposable, enrollment, quickstart] = await Promise.all([
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
    read('src/modules/admin/composables/useBackupEnrollment.js'),
    read('src/modules/admin/composables/useDatabaseBackupsPage.js'),
    read('src/modules/admin/domain/backupEnrollment.js'),
    read('../docs/deployment/BACKUP_SETUP_QUICKSTART.md'),
  ])

  assert.match(page, /v-if="!connectionReady"/)
  assert.match(page, /operation="prepare_enrollment"/)
  assert.match(page, /operation="apply_enrollment"/)
  assert.match(page, /operation="backup"/)
  assert.match(composable, /prepareBackupEnrollment\(token\)/)
  assert.match(composable, /applyBackupEnrollment\([^\n]+, token\)/)
  assert.match(composable, /status\.value\.operation === 'prepare_enrollment'/)
  assert.match(composable, /\['queued', 'running'\]\.includes\(status\.value\.state\)/)
  assert.doesNotMatch(page, /!canApplyEnrollment \|\| !hasHostApproval/)
  assert.match(pageComposable, /approvalPlaceholder/)
  assert.match(enrollment, /provisioner_base64/)
  assert.doesNotMatch(enrollment, /github\.com|curl --fail/)
  assert.match(enrollment, /sha256sum -c/)
  assert.match(quickstart, /Recovery Tool is \*\*not\*\* required/)
  assert.match(quickstart, /before every normal\s+update/)
})

test('host-approved requests retain CSRF and capability headers', async () => {
  const [client, security] = await Promise.all([
    read('src/shared/api/client.js'),
    read('../spring-api/src/main/java/eu/royalblackwater/api/config/SecurityConfiguration.java'),
  ])

  assert.match(client, /\.\.\.options,[\s\S]*headers,[\s\S]*\}\)/)
  assert.match(security, /"X-XSRF-TOKEN", "X-RBF-Host-Capability"/)
})
