import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import { systemLogManagementMessages } from '../src/locales/messages/systemLogManagement.js'

async function source(path) {
  return (await readFile(new URL(path, import.meta.url), 'utf8')).replaceAll('\r\n', '\n')
}

const apiSource = await source('../src/modules/admin/api/admin.js')
const panelSource = await source('../src/modules/admin/components/SystemLogPanel.vue')
const logsSource = await source('../src/modules/admin/composables/useAdminLogs.js')
const dashboardSource = await source('../src/modules/admin/components/SecurityLogDashboard.vue')
const pageSource = await source('../src/modules/admin/pages/AdminPage.vue')
const styleSource = await source('../src/modules/admin/styles/staffWorkspace.css')


test('blocked-IP noise is hidden by default and can be deliberately revealed', () => {
  assert.ok(logsSource.includes('const logIncludeBlocked = ref(false)'))
  assert.ok(logsSource.includes('includeBlocked: logIncludeBlocked.value'))
  assert.ok(logsSource.includes('logIncludeBlocked.value = Boolean(ipAddress)'))
  assert.ok(apiSource.includes('include_blocked: includeBlocked'))
  assert.ok(panelSource.includes('v-model="logIncludeBlocked"'))
  assert.ok(panelSource.includes("t('admin.logs.blockedHidden')"))
  assert.ok(dashboardSource.includes('includeBlocked: props.includeBlocked'))
})


test('system log deletion remains explicit, confirmed and admin-scoped', () => {
  assert.ok(pageSource.includes("activeTab === 'logs' && isAdmin"))
  assert.ok(apiSource.includes('export function deleteAdminLog(id)'))
  assert.ok(apiSource.includes('export function deleteFilteredAdminLogs'))
  assert.ok(apiSource.includes('confirm: true'))
  assert.ok(logsSource.includes('if (!isAdmin.value || !id) return false'))
  assert.ok(logsSource.includes('if (!isAdmin.value) return 0'))
  assert.ok(panelSource.includes('confirmFilteredDelete'))
  assert.ok(panelSource.includes('pendingEntryDeleteId'))
  assert.ok(panelSource.includes("t('admin.logs.deleteFilteredConfirmTitle')"))
  assert.ok(panelSource.includes("t('admin.logs.deleteOneConfirm')"))
})


test('the extracted log workspace has responsive, non-overlapping controls', () => {
  for (const selector of [
    '.system-log-panel',
    '.system-log-heading-actions',
    '.system-log-filter-grid',
    '.system-log-blocked-toggle',
    '.system-log-entry-actions',
  ]) {
    assert.ok(styleSource.includes(selector), selector)
  }
  assert.ok(styleSource.includes('grid-template-columns: repeat(4, minmax(0, 1fr))'))
  assert.ok(styleSource.includes('@media (max-width: 760px)'))
})


test('system log management copy is complete for every supported locale', () => {
  for (const locale of ['en', 'de', 'fr', 'es', 'pt', 'ru', 'cn']) {
    assert.ok(systemLogManagementMessages[locale]?.admin?.logs?.deleteFiltered, locale)
    assert.ok(systemLogManagementMessages[locale]?.admin?.logs?.includeBlocked, locale)
    assert.ok(systemLogManagementMessages[locale]?.admin?.audit?.entities?.app_log, locale)
  }
})
