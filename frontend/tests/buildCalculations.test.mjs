import test from 'node:test'
import assert from 'node:assert/strict'

import {
  calculateBuildStatRows,
  calculateUpgradeSlotAccess,
  sumEffects,
} from '../src/modules/builds/buildCalculations.js'


test('sumEffects combines selected catalog effects without mutating inputs', () => {
  const sails = { speed_knots: 4.1, cruising_speed_gain_pct: -20 }
  const lantern = { speed_pct: 5, armor_pct: 5 }

  assert.deepEqual(sumEffects(sails, lantern), {
    speed_knots: 4.1,
    cruising_speed_gain_pct: -20,
    speed_pct: 5,
    armor_pct: 5,
  })
  assert.deepEqual(sails, { speed_knots: 4.1, cruising_speed_gain_pct: -20 })
})


test('calculateBuildStatRows applies percentage before the flat calculator bonus', () => {
  const [speed] = calculateBuildStatRows({
    ship: { speed_knots: 10 },
    definitions: [{
      key: 'speed',
      base_field: 'speed_knots',
      pct_effect: 'speed_pct',
      flat_effect: 'speed_knots',
      calculation_flat_effect: 'speed_knots',
      precision: 1,
      positive_is_good: true,
    }],
    effects: { speed_pct: 5, speed_knots: 4.1 },
  })

  assert.equal(speed.base, 10)
  assert.equal(speed.effective, 14.6)
})


test('research reward unlocks one optional slot and reports its availability', () => {
  assert.deepEqual(
    calculateUpgradeSlotAccess({ shipUpgradeSlots: 4, researchUpgradeSlotUnlocked: true }),
    {
      baseSlots: 4,
      effectSlots: 0,
      researchSlots: 1,
      shipExtraSlots: 0,
      slot5Unlocked: true,
      slot6Available: false,
      availableSlots: 5,
    },
  )
})
