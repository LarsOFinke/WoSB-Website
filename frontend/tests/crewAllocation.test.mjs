import test from 'node:test'
import assert from 'node:assert/strict'

import {
  crewSliderMax,
  crewTotal,
  normalizeCrewAllocation,
  sailingEfficiencyPercent,
  setCrewAllocationValue,
} from '../src/modules/builds/crewAllocation.js'


test('Anson allocation stays within 160 crew and preserves the sailor target', () => {
  const allocation = normalizeCrewAllocation(
    { sailors: 80, musketeers: 0, soldiers: 80, mercenaries: 12 },
    160,
    80,
  )

  assert.deepEqual(allocation, { sailors: 80, musketeers: 0, soldiers: 80, mercenaries: 0 })
  assert.equal(crewTotal(allocation), 160)
  assert.equal(sailingEfficiencyPercent(allocation.sailors, 80), 100)
})


test('crew input is capped only by remaining capacity, not the sailor minimum', () => {
  const allocation = { sailors: 40, musketeers: 20, soldiers: 20, mercenaries: 0 }
  assert.equal(crewSliderMax(allocation, 'soldiers', 160, 80), 100)
  assert.equal(crewSliderMax(allocation, 'sailors', 160, 80), 120)
  assert.deepEqual(
    setCrewAllocationValue(allocation, 'sailors', 110, 160, 80),
    { sailors: 110, musketeers: 20, soldiers: 20, mercenaries: 0 },
  )
})
