import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')

test('privacy-sensitive staff tabs are admin-only in the UI', () => {
  for (const tab of ['status', 'logs', 'ip-blocks', 'audit', 'integrations']) {
    assert.match(source, new RegExp(`v-if="isAdmin"[^>]+activeTab === '${tab}'`))
    assert.ok(source.includes(`activeTab === '${tab}' && isAdmin`))
  }
})

test('access review remains available to moderators', () => {
  assert.ok(source.includes("activeTab === 'registrations'"))
  assert.ok(source.includes("t('admin.tabs.registrations')"))
  assert.doesNotMatch(source, /v-if="isAdmin"[^>]+activeTab === 'registrations'/)
  assert.ok(source.includes("activeTab === 'registrations' && isStaff"))
  assert.ok(source.includes("async function loadRegistrations() {\n  if (!isStaff.value) return"))
})

test('moderators are not sent admin-only status and log requests on mount', () => {
  assert.ok(source.includes("async function loadStatus() {\n  if (!isAdmin.value) return"))
  assert.ok(source.includes("async function loadLogs() {\n  if (!isAdmin.value) return"))
  assert.ok(source.includes("activeTab.value = isAdmin.value ? 'status' : 'registrations'"))
})
