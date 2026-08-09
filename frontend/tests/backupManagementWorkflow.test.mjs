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
  assert.doesNotMatch(page, /enrollment|private_key|local\/restore|arm-admin-restore/)
  assert.doesNotMatch(composable, /useBackupEnrollment|private_key|restoreLocal|configureBackup|discoverBackup/)
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

test('the browser surface does not expose recovery transfers or restore controls', async () => {
  const page = await read('src/modules/admin/pages/DatabaseBackupsPage.vue')
  assert.doesNotMatch(page, /local\/restore|restoreDatabase|restoreFiles|type="password"|approval_token/)
  assert.match(page, /runBackup/)
  assert.match(page, /status\.artifacts/)
})
