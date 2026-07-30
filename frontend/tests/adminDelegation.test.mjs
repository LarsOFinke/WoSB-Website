import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const composablePath = new URL('../src/modules/admin/composables/useAdminUsers.js', import.meta.url)
const pagePath = new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url)

test('only the bootstrap administrator receives administrator delegation controls', async () => {
  const [composable, page] = await Promise.all([readFile(composablePath, 'utf8'), readFile(pagePath, 'utf8')])
  assert.match(composable, /row\.role === 'admin'\) return canGrantAdmin\(\)/)
  assert.match(composable, /row\.is_bootstrap_admin/)
  assert.match(composable, /row\.role !== 'admin'/)
  assert.match(page, /v-if="canGrantAdmin\(\)" value="admin"/)
  assert.match(page, /v-if="canToggleUserActive\(row\)"/)
})
