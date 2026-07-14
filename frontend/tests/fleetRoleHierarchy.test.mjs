import assert from 'node:assert/strict'
import fs from 'node:fs'
import test from 'node:test'

const source = fs.readFileSync(new URL('../src/modules/fleet/pages/FleetManagePage.vue', import.meta.url), 'utf8')

test('fleet management renders backend-provided membership permissions', () => {
  assert.match(source, /membership\?\.management/)
  assert.match(source, /can_change_role/)
  assert.match(source, /can_change_status/)
  assert.match(source, /can_edit_directory/)
  assert.match(source, /assignable_roles/)
})

test('protected roles are shown instead of editable controls', () => {
  assert.match(source, /fleet-protection-notice/)
  assert.match(source, /protectionReasons/)
  assert.match(source, /fleet-hierarchy-policy/)
})
