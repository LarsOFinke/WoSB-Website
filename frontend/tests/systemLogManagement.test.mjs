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
const blockPanelSource = await source('../src/modules/admin/components/IpBlockManagementPanel.vue')
const styleSource = await source('../src/modules/admin/styles/staffWorkspace.css')


test('the admin UI exposes only aggregated IP-ban candidates', () => {
  assert.ok(pageSource.includes("activeTab === 'logs' && isAdmin"))
  assert.ok(apiSource.includes('export function getSecurityDashboard'))
  assert.ok(!apiSource.includes('export function listAdminLogs'))
  assert.ok(!apiSource.includes('export function getAdminLogSummary'))
  assert.ok(!apiSource.includes('export function deleteAdminLog'))
  assert.ok(!apiSource.includes('export function deleteFilteredAdminLogs'))
  assert.ok(panelSource.includes('security-privacy-notice'))
  assert.ok(panelSource.includes('SecurityLogDashboard'))
  assert.ok(!panelSource.includes('staff-log-list'))
  assert.ok(!panelSource.includes('expandedLogId'))
})


test('routes, user agents and raw request details are absent from the candidate view', () => {
  for (const forbidden of ['top_paths', 'distinct_paths', 'user_agent', 'query_string', 'request_id', 'entry.path', 'entry.exception']) {
    assert.ok(!dashboardSource.includes(forbidden), forbidden)
    assert.ok(!panelSource.includes(forbidden), forbidden)
  }
  for (const required of ['reconnaissance', 'login_failures', 'rate_limits', 'event_count', 'block-ip']) {
    assert.ok(dashboardSource.includes(required), required)
  }
  assert.ok(!logsSource.includes('logPath'))
  assert.ok(!logsSource.includes('logLevel'))
  assert.ok(!logsSource.includes('logIncludeBlocked'))
  assert.ok(!blockPanelSource.includes('view-logs'))
})


test('the privacy notice is present and responsive', () => {
  assert.ok(styleSource.includes('.security-privacy-notice'))
  assert.ok(styleSource.includes('@media (max-width: 760px)'))
})


test('purpose limitation copy exists for every supported locale', () => {
  for (const locale of ['en', 'de', 'fr', 'es', 'pt', 'ru', 'cn']) {
    assert.ok(systemLogManagementMessages[locale]?.admin?.logs?.privacyTitle, locale)
    assert.ok(systemLogManagementMessages[locale]?.admin?.logs?.privacyText, locale)
    assert.ok(systemLogManagementMessages[locale]?.admin?.audit?.entities?.security_event, locale)
  }
})
