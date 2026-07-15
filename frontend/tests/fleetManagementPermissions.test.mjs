import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

test('fleet admirals receive a dedicated custom role administration area', async () => {
  const page = await readFile(new URL('../src/modules/fleet/pages/FleetManagePage.vue', import.meta.url), 'utf8')
  const composable = await readFile(new URL('../src/modules/fleet/composables/useFleetManagePage.js', import.meta.url), 'utf8')
  const api = await readFile(new URL('../src/modules/fleet/api/fleet.js', import.meta.url), 'utf8')
  assert.ok(page.includes("activeTab === 'roles' && canManageRoles"))
  assert.ok(composable.includes("currentMembership.value?.role === 'fleet_admiral'"))
  assert.ok(api.includes('createFleetRole'))
  assert.ok(api.includes('deleteFleetRole'))
})
