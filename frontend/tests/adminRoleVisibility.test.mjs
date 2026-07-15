import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const pageSource = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')
const workspaceSource = await readFile(new URL('../src/modules/admin/composables/useAdminWorkspace.js', import.meta.url), 'utf8')
const registrationsSource = await readFile(new URL('../src/modules/admin/composables/useAdminRegistrations.js', import.meta.url), 'utf8')
const logsSource = await readFile(new URL('../src/modules/admin/composables/useAdminLogs.js', import.meta.url), 'utf8')
const operationsSource = await readFile(new URL('../src/modules/admin/composables/useAdminOperations.js', import.meta.url), 'utf8')

test('privacy-sensitive staff tabs are admin-only in navigation and content', () => {
  assert.ok(workspaceSource.includes("const ADMIN_ONLY_TABS = new Set(['status', 'logs', 'ip-blocks', 'audit', 'integrations', 'users'])"))
  for (const tab of ['status', 'logs', 'ip-blocks', 'audit', 'integrations', 'users']) {
    assert.match(workspaceSource, new RegExp(`key: '${tab}'.+adminOnly: true`))
    assert.ok(pageSource.includes(`activeTab === '${tab}' && isAdmin`))
  }
  assert.ok(workspaceSource.includes('tabs: group.tabs.filter((tab) => !tab.adminOnly || isAdmin.value)'))
})

test('access review and shared work areas remain available to moderators', () => {
  for (const tab of ['overview', 'registrations', 'calendar', 'content', 'builds']) {
    assert.match(workspaceSource, new RegExp(`key: '${tab}'`))
  }
  assert.ok(pageSource.includes("activeTab === 'registrations' && isStaff"))
  assert.match(registrationsSource, /async function loadRegistrations\(\) \{\n\s+if \(!isStaff\.value\) return/)
})

test('moderators are not sent admin-only overview requests', () => {
  assert.match(operationsSource, /async function loadStatus\(\) \{\n\s+if \(!isAdmin\.value\) return/)
  assert.match(logsSource, /async function loadLogs\(\) \{\n\s+if \(!isAdmin\.value\) return/)
  assert.match(operationsSource, /async function loadAdminOverviewMetrics\(\) \{\n\s+if \(!isAdmin\.value\) return/)
  assert.match(workspaceSource, /if \(isAdmin\.value\) \{[\s\S]*loadStatus\(\)[\s\S]*loadUsers\(\)[\s\S]*loadAdminOverviewMetrics\(\)/)
  assert.ok(workspaceSource.includes("activeTab.value = 'overview'"))
})
