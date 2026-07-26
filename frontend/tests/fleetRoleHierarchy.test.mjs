import assert from 'node:assert/strict'
import fs from 'node:fs'
import test from 'node:test'

const pageSource = fs.readFileSync(new URL('../src/modules/fleet/pages/FleetManagePage.vue', import.meta.url), 'utf8')
const memberRowSource = fs.readFileSync(new URL('../src/modules/fleet/components/FleetMemberRow.vue', import.meta.url), 'utf8')
const modelSource = fs.readFileSync(new URL('../src/modules/fleet/composables/useFleetManagePage.js', import.meta.url), 'utf8')
const domainSource = fs.readFileSync(new URL('../src/modules/fleet/domain/fleetMemberships.js', import.meta.url), 'utf8')
const behaviorSource = `${modelSource}\n${domainSource}`

test('fleet management renders backend-provided membership permissions', () => {
  assert.match(behaviorSource, /membership\?\.management/)
  assert.match(behaviorSource, /can_change_role/)
  assert.match(behaviorSource, /can_change_status/)
  assert.match(behaviorSource, /can_edit_directory/)
  assert.match(behaviorSource, /assignable_roles/)
  assert.match(pageSource, /managementFor\(membership\)/)
})

test('protected roles are shown instead of editable controls', () => {
  assert.match(memberRowSource, /fleet-refresh-protection/)
  assert.match(modelSource, /protectionReasons/)
  assert.match(pageSource, /fleet-refresh-hierarchy/)
})
