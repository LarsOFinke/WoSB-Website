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

test('founder is a seeded special role and is exposed by the public leadership route', async () => {
  const [api, seed, publicPage] = await Promise.all([
    readFile(new URL('../src/modules/fleet/api/fleet.js', import.meta.url), 'utf8'),
    readFile(new URL('../../spring-api/src/main/resources/seed/system/roles.json', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/fleet/pages/FleetPublicPage.vue', import.meta.url), 'utf8'),
  ])
  assert.match(api, /'founder'/)
  assert.match(seed, /"code": "founder"/)
  assert.match(seed, /"is_leadership": true/)
  assert.match(publicPage, /leader\.role_label \|\| t\(`fleets\.roles\.\$\{leader\.role\}`\)/)
})
