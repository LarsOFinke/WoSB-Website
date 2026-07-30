import test from 'node:test'
import assert from 'node:assert/strict'

import {
  calculateBuildStatRows,
  calculateBuildUpgradeSlotAccess,
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


test('upgrade add-on slot unlocks one optional slot and reports its availability', () => {
  assert.deepEqual(
    calculateUpgradeSlotAccess({ shipUpgradeSlots: 4, researchUpgradeSlots: 1 }),
    {
      baseSlots: 4,
      effectSlots: 0,
      researchSlots: 1,
      shipExtraSlots: 0,
      slot5Unlocked: true,
      slot6Available: false,
      slot7Available: false,
      slot8Available: false,
      availableSlots: 5,
    },
  )
})



test('Structural Expansion grants both tooltip slots while occupying its selected position', () => {
  const access = calculateBuildUpgradeSlotAccess({
    form: {
      research_upgrade_slot_unlocked: true,
      upgrade_5: 'Structural Expansion',
    },
    shipUpgradeSlots: 5,
    effectForUpgrade: (name) => name === 'Structural Expansion' ? { extra_upgrade_slots: 2 } : {},
    researchUpgradeSlots: 1,
  })

  assert.equal(access.expansionUnlockSlots, 2)
  assert.equal(access.availableSlots, 7)
  assert.equal(access.slot7Available, true)
  assert.equal(access.slot8Available, false)
})

test('Ice Lantern applies all three current-event bonuses to Leopard', () => {
  const rows = calculateBuildStatRows({
    ship: { speed_knots: 9.6, hold_capacity: 16500, durability: 2040 },
    definitions: [
      { key: 'speed', base_field: 'speed_knots', pct_effect: 'speed_pct', precision: 1 },
      { key: 'hold', base_field: 'hold_capacity', pct_effect: 'hold_capacity_pct', precision: 0 },
      { key: 'durability', base_field: 'durability', pct_effect: 'hull_hp_pct', precision: 0 },
    ],
    effects: { speed_pct: 5, hold_capacity_pct: 5, hull_hp_pct: 5 },
  })

  assert.deepEqual(rows.map((row) => row.effective), [10.1, 17325, 2142])
})

test('flat durability and armor upgrade values are applied after percentages', () => {
  const rows = calculateBuildStatRows({
    ship: { durability: 1000, armor: 4 },
    definitions: [
      {
        key: 'durability',
        base_field: 'durability',
        pct_effect: 'hull_hp_pct',
        calculation_flat_effect: 'durability',
        precision: 0,
      },
      {
        key: 'armor',
        base_field: 'armor',
        pct_effect: 'armor_pct',
        calculation_flat_effect: 'armor',
        precision: 1,
      },
    ],
    effects: { hull_hp_pct: 10, durability: 150, armor_pct: -10, armor: 15 },
  })

  assert.deepEqual(rows.map((row) => row.effective), [1250, 18.6])
})


test('research, Structural Expansion and a ship extra stack to eight slots', () => {
  assert.deepEqual(
    calculateUpgradeSlotAccess({
      shipUpgradeSlots: 6,
      researchUpgradeSlots: 1,
      unlockEffectSlots: 2,
    }),
    {
      baseSlots: 4,
      effectSlots: 2,
      researchSlots: 1,
      shipExtraSlots: 1,
      slot5Unlocked: true,
      slot6Available: true,
      slot7Available: true,
      slot8Available: true,
      availableSlots: 8,
    },
  )
})

test('La Couronne verified equipment stack matches the in-game speed range', () => {
  const effectSets = [
    { speed_pct: 5, armor_pct: 5 },
    { speed_pct: 4, armor_pct: -15 },
    { speed_knots: 4.1 },
  ]
  const rows = calculateBuildStatRows({
    ship: { speed_min_knots: 7.6, speed_knots: 10.6, armor: 5.5 },
    definitions: [
      {
        key: 'speed_min_knots',
        base_field: 'speed_min_knots',
        pct_effect: 'speed_pct',
        precision: 1,
      },
      {
        key: 'speed_knots',
        base_field: 'speed_knots',
        pct_base_field: 'speed_min_knots',
        pct_effect: 'speed_pct',
        calculation_flat_effect: 'speed_knots',
        precision: 1,
      },
      {
        key: 'armor',
        base_field: 'armor',
        pct_effect: 'armor_pct',
        precision: 1,
      },
    ],
    effects: { speed_pct: 9, speed_knots: 4.1, armor_pct: -10 },
    effectSets,
  })

  assert.deepEqual(rows.map((row) => row.effective), [8.3, 15.4, 4.9])
  assert.deepEqual(rows[1].percent_modifier, 9.2)
  assert.deepEqual(rows[1].flat_modifier, 4.1)
  assert.deepEqual(rows[1].modifier, 4.8)
})
