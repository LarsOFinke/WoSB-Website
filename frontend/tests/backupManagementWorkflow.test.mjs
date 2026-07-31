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
  assert.match(composable, /discoverBackupHost/)
  assert.match(composable, /configureBackupConnection/)
  assert.match(composable, /testBackupConnection/)
  assert.match(composable, /runApplicationBackup/)
  assert.match(composable, /scanLocalDatabaseBackups/)
  assert.match(composable, /restoreLocalDatabaseBackup/)
  assert.match(composable, /window\.confirm\(t\('admin\.backups\.confirmRun'\)\)/)
  assert.match(composable, /private_key: form\.private_key\.trim\(\) \|\| null/)
})

test('backup connection API exposes no browser-side secret persistence', async () => {
  const [api, page, messages] = await Promise.all([
    read('src/modules/admin/api/admin.js'),
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
    read('src/locales/messages/backupManagement.js'),
  ])

  assert.match(api, /get\('\/admin\/backups\/status'\)/)
  assert.match(api, /put\('\/admin\/backups\/configuration'/)
  assert.match(api, /post\('\/admin\/backups\/run'/)
  assert.match(api, /post\('\/admin\/backups\/local\/scan'/)
  assert.match(api, /post\('\/admin\/backups\/local\/restore'/)
  assert.doesNotMatch(page, /localStorage|sessionStorage/)
  assert.match(page, /autocomplete="off"/)
  for (const locale of ['en', 'de', 'fr', 'es', 'pt', 'ru', 'cn']) {
    assert.match(messages, new RegExp(`\\b${locale}: \\{`))
  }
  assert.match(messages, /recovery: 'Encrypted disaster-recovery bundle'/)
  assert.match(messages, /recovery: 'Verschlüsseltes Disaster-Recovery-Bundle'/)
})

test('database restore requires an opaque catalog id and host approval token', async () => {
  const [page, composable, extensionMessages] = await Promise.all([
    read('src/modules/admin/pages/DatabaseBackupsPage.vue'),
    read('src/modules/admin/composables/useDatabaseBackupsPage.js'),
    read('src/locales/messages/backupRecoveryExtensions.js'),
  ])

  assert.match(page, /arm-admin-restore\.sh/)
  assert.match(page, /user\?\.is_bootstrap_admin|isBootstrapAdmin/)
  assert.match(page, /type="password"/)
  assert.doesNotMatch(page, /backup\.path|local_path|file_path/)
  assert.match(composable, /RESTORE_CONFIRMATION = 'RESTORE DATABASE'/)
  assert.match(composable, /APPROVAL_TOKEN_PATTERN/)
  assert.match(composable, /backup_id: restoreForm\.backup_id/)
  assert.match(extensionMessages, /Two-person-style host approval/)
  assert.match(extensionMessages, /Zusätzliche Host-Freigabe/)
})

