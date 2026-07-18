import assert from 'node:assert/strict'
import test from 'node:test'

import { BUILD_DISCOVERY_VALUES } from '../src/modules/builds/domain/buildDiscovery.js'
import { GUIDE_CATEGORY_VALUES } from '../src/modules/guides/domain/guideDiscovery.js'
import {
  composeSpecialistSelection,
  splitSpecialistSelection,
} from '../src/modules/builds/domain/specialistSelection.js'

test('build discovery taxonomy contains unique filter values', () => {
  assert.equal(BUILD_DISCOVERY_VALUES.length, 14)
  assert.equal(new Set(BUILD_DISCOVERY_VALUES).size, BUILD_DISCOVERY_VALUES.length)
  assert.ok(BUILD_DISCOVERY_VALUES.includes('port_battle'))
  assert.ok(BUILD_DISCOVERY_VALUES.includes('imperial'))
})

test('guide taxonomy keeps legacy categories and adds discovery topics', () => {
  for (const category of ['general', 'builds', 'economy', 'new_captains', 'fleet_operations', 'port_battles']) {
    assert.ok(GUIDE_CATEGORY_VALUES.includes(category))
  }
})

test('Ginger uses an extra specialist position outside the four regular slots', () => {
  const slots = composeSpecialistSelection([
    { item: 'Doctor' }, { item: 'Gunner' }, { item: 'Cook' }, { item: 'Navigator' }, { item: 'Scout' },
  ], true, false)
  const selection = splitSpecialistSelection(slots)
  assert.equal(selection.regular.length, 4)
  assert.equal(selection.gingerSelected, true)
  assert.equal(slots.length, 5)
})
