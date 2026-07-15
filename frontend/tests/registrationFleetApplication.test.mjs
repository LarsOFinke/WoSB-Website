import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const registerPage = readFileSync(new URL('../src/modules/accounts/pages/RegisterPage.vue', import.meta.url), 'utf8')
const adminPage = readFileSync(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')


test('registration can submit an optional official fleet application', () => {
  assert.match(registerPage, /wants_fleet_membership: applyToFleet/)
  assert.match(registerPage, /fleet_id: applyToFleet \? officialFleet\.value\.id : null/)
  assert.match(registerPage, /fleet_application_note: applyToFleet \? fleetApplicationNote\.value : null/)
  assert.match(registerPage, /joinOfficialFleetExistingMemberHint/)
})


test('access review surfaces the attached fleet application', () => {
  assert.match(adminPage, /request\.wants_fleet_membership/)
  assert.match(adminPage, /request\.fleet_application_note/)
  assert.match(adminPage, /admin\.registrations\.fleetApplication/)
})
