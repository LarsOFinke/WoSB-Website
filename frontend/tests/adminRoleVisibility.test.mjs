import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')

test('privacy-sensitive staff tabs are admin-only in navigation and content', () => {
  assert.ok(source.includes("const ADMIN_ONLY_TABS = new Set(['status', 'logs', 'ip-blocks', 'audit', 'integrations', 'users'])"))
  for (const tab of ['status', 'logs', 'ip-blocks', 'audit', 'integrations', 'users']) {
    assert.match(source, new RegExp(`key: '${tab}'.+adminOnly: true`))
    assert.ok(source.includes(`activeTab === '${tab}' && isAdmin`))
  }
  assert.ok(source.includes('tabs: group.tabs.filter((tab) => !tab.adminOnly || isAdmin.value)'))
})

test('access review and shared work areas remain available to moderators', () => {
  for (const tab of ['overview', 'registrations', 'calendar', 'content', 'builds']) {
    assert.match(source, new RegExp(`key: '${tab}'`))
  }
  assert.ok(source.includes("activeTab === 'registrations' && isStaff"))
  assert.ok(source.includes("async function loadRegistrations() {\n  if (!isStaff.value) return"))
})

test('moderators are not sent admin-only overview requests', () => {
  assert.ok(source.includes("async function loadStatus() {\n  if (!isAdmin.value) return"))
  assert.ok(source.includes("async function loadLogs() {\n  if (!isAdmin.value) return"))
  assert.ok(source.includes("async function loadAdminOverviewMetrics() {\n  if (!isAdmin.value) return"))
  assert.ok(source.includes("if (isAdmin.value) tasks.push(loadStatus(), loadUsers(), loadAdminOverviewMetrics())"))
  assert.ok(source.includes("activeTab.value = 'overview'"))
})
