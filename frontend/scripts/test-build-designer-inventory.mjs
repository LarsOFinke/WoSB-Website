import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const frontendRoot = resolve(scriptDir, '..')

import {
  emptyInventorySlot,
  isWeaponInventoryField,
  normalizeInventorySlots,
  reconcileInventorySlots,
  selectInventoryItem,
  setInventoryQuantity,
} from '../src/modules/builds/inventorySlots.js'

assert.equal(isWeaponInventoryField('consumable_slots'), false)
assert.equal(isWeaponInventoryField('ammunition_slots'), false)
assert.equal(isWeaponInventoryField('hold_slots'), false)
assert.equal(isWeaponInventoryField('special_crew_slots'), false)
assert.equal(isWeaponInventoryField('port_weapon_slots'), true)

const initial = [emptyInventorySlot()]
const selected = selectInventoryItem(initial, 0, 'Repair Kit', 3)
assert.deepEqual(selected, [
  { item: 'Repair Kit', quantity: 1 },
  { item: '', quantity: 1 },
])
assert.equal(initial[0].item, '', 'selection must not depend on mutating the original DOM-bound slot')

const second = selectInventoryItem(selected, 1, 'Rum Ration', 3)
assert.deepEqual(second, [
  { item: 'Repair Kit', quantity: 1 },
  { item: 'Rum Ration', quantity: 1 },
  { item: '', quantity: 1 },
])

const withQuantity = setInventoryQuantity(second, 0, 12, 3)
assert.equal(withQuantity[0].quantity, 12)
assert.equal(withQuantity[1].item, 'Rum Ration')

assert.deepEqual(normalizeInventorySlots([{ item: '  Repair Kit  ', quantity: 0 }, { item: '', quantity: 8 }]), [
  { item: 'Repair Kit', quantity: 1 },
])
assert.deepEqual(reconcileInventorySlots([{ item: 'Mortar', quantity: 1 }], 0), [])
assert.deepEqual(
  reconcileInventorySlots([{ item: 'Wrong Slot', quantity: 1 }], 2, { isItemAllowed: (item) => item !== 'Wrong Slot' }),
  [{ item: '', quantity: 1 }],
)


import {
  crewSliderMax,
  crewTotal,
  normalizeCrewAllocation,
  setCrewAllocationValue,
} from '../src/modules/builds/crewAllocation.js'

const crew = normalizeCrewAllocation(
  { sailors: 80, musketeers: 20, soldiers: 15, mercenaries: 10 },
  100,
  60,
)
assert.deepEqual(crew, { sailors: 80, musketeers: 20, soldiers: 0, mercenaries: 0 })
assert.equal(crewTotal(crew), 100)
assert.equal(crewSliderMax(crew, 'soldiers', 100, 60), 0)
assert.equal(crewSliderMax(crew, 'sailors', 100, 60), 80)

const reassigned = setCrewAllocationValue(crew, 'musketeers', 5, 100, 60)
assert.deepEqual(reassigned, { sailors: 80, musketeers: 5, soldiers: 0, mercenaries: 0 })
assert.equal(crewSliderMax(reassigned, 'soldiers', 100, 60), 15)

const reducedCapacity = normalizeCrewAllocation(
  { sailors: 90, musketeers: 20, soldiers: 15, mercenaries: 10 },
  75,
  65,
)
assert.deepEqual(reducedCapacity, { sailors: 75, musketeers: 0, soldiers: 0, mercenaries: 0 })
assert.equal(crewTotal(reducedCapacity), 75)

import { calculateBuildStatRows, calculateUpgradeSlotAccess, sumEffects } from '../src/modules/builds/buildCalculations.js'

assert.deepEqual(sumEffects({ speed_pct: 4 }, { speed_pct: 3, reload_pct: 2 }), {
  speed_pct: 7,
  reload_pct: 2,
})

const equipmentStatDefinitions = [
  { key: 'durability', base_field: 'durability', pct_effect: 'hull_hp_pct', precision: 0, positive_is_good: true },
  { key: 'speed_knots', base_field: 'speed_knots', pct_effect: 'speed_pct', calculation_flat_effect: 'speed_knots', precision: 1, positive_is_good: true },
  { key: 'speed_bonus_knots', base_field: null, flat_effect: 'speed_knots', precision: 1, positive_is_good: true },
  { key: 'cruising_speed_gain_pct', base_field: null, flat_effect: 'cruising_speed_gain_pct', precision: 0, positive_is_good: true },
  { key: 'cruising_maneuverability_pct', base_field: null, flat_effect: 'cruising_maneuverability_pct', precision: 0, positive_is_good: true },
  { key: 'cruising_turn_speed_penalty_pct', base_field: null, flat_effect: 'cruising_turn_speed_penalty_pct', precision: 0, positive_is_good: true },
  { key: 'strong_wind_cruising_speed_bonus_knots', base_field: null, flat_effect: 'strong_wind_cruising_speed_bonus_knots', precision: 1, positive_is_good: true },
  { key: 'turning_cruising_speed_bonus_knots', base_field: null, flat_effect: 'turning_cruising_speed_bonus_knots', precision: 1, positive_is_good: true },
  { key: 'running_before_wind_speed_penalty_pct', base_field: null, flat_effect: 'running_before_wind_speed_penalty_pct', precision: 0, positive_is_good: true },
  { key: 'broad_reach_cruising_speed_bonus_pct', base_field: null, flat_effect: 'broad_reach_cruising_speed_bonus_pct', precision: 0, positive_is_good: true },
  { key: 'maneuverability', base_field: 'maneuverability', pct_effect: 'turn_rate_pct', calculation_flat_effect: 'maneuverability', precision: 0, positive_is_good: true },
  { key: 'maneuverability_bonus', base_field: null, flat_effect: 'maneuverability', precision: 0, positive_is_good: true },
  { key: 'armor', base_field: 'armor', pct_effect: 'armor_pct', precision: 1, positive_is_good: true },
  { key: 'hold_capacity', base_field: 'hold_capacity', pct_effect: 'hold_capacity_pct', calculation_flat_effect: 'hold_capacity', precision: 0, positive_is_good: true },
  { key: 'damage_pct', base_field: null, flat_effect: 'damage_pct', precision: 0, positive_is_good: true },
  { key: 'exp_loot_pct', base_field: null, flat_effect: 'exp_loot_pct', precision: 0, positive_is_good: true },
]
const equipmentShip = {
  durability: 1000,
  speed_knots: 10,
  maneuverability: 80,
  armor: 12,
  hold_capacity: 5000,
}

function statRowsByKey(effects) {
  return Object.fromEntries(calculateBuildStatRows({
    ship: equipmentShip,
    definitions: equipmentStatDefinitions,
    effects,
  }).map((row) => [row.key, row]))
}

const cheapRows = statRowsByKey({ speed_knots: 2 })
assert.equal(cheapRows.speed_knots.effective, 12)
const stitchedRows = statRowsByKey({ speed_knots: 2.4 })
assert.equal(stitchedRows.speed_knots.effective, 12.4)
const ultraLightRows = statRowsByKey({
  speed_knots: 2.4,
  cruising_maneuverability_pct: 15,
  cruising_turn_speed_penalty_pct: -30,
})
assert.equal(ultraLightRows.speed_knots.effective, 12.4)
assert.equal(ultraLightRows.cruising_maneuverability_pct.modifier, 15)
assert.equal(ultraLightRows.cruising_turn_speed_penalty_pct.modifier, -30)
assert.equal(ultraLightRows.cruising_turn_speed_penalty_pct.isDebuff, true)
const stormSailRows = statRowsByKey({ speed_knots: 2.7, strong_wind_cruising_speed_bonus_knots: 2.5 })
assert.equal(stormSailRows.speed_knots.effective, 12.7)
assert.equal(stormSailRows.strong_wind_cruising_speed_bonus_knots.modifier, 2.5)
const eliteRows = statRowsByKey({ speed_knots: 2.8 })
assert.equal(eliteRows.speed_knots.effective, 12.8)
const tackingRows = statRowsByKey({
  speed_knots: 2.8,
  turning_cruising_speed_bonus_knots: 2,
  cruising_maneuverability_pct: -20,
})
assert.equal(tackingRows.speed_knots.effective, 12.8)
assert.equal(tackingRows.turning_cruising_speed_bonus_knots.modifier, 2)
assert.equal(tackingRows.cruising_maneuverability_pct.isDebuff, true)
const reefedRows = statRowsByKey({
  speed_knots: 2.9,
  running_before_wind_speed_penalty_pct: -100,
  broad_reach_cruising_speed_bonus_pct: -50,
})
assert.equal(reefedRows.speed_knots.effective, 12.9)
assert.equal(reefedRows.running_before_wind_speed_penalty_pct.isDebuff, true)
assert.equal(reefedRows.broad_reach_cruising_speed_bonus_pct.isDebuff, true)
const tarpaulinRows = statRowsByKey({ speed_knots: 3.1, maneuverability: -2 })
assert.equal(tarpaulinRows.speed_knots.effective, 13.1)
assert.equal(tarpaulinRows.maneuverability.effective, 78)
assert.equal(tarpaulinRows.maneuverability_bonus.isDebuff, true)
const raidingRows = statRowsByKey({
  speed_knots: 4.1,
  cruising_maneuverability_pct: -20,
  cruising_speed_gain_pct: -20,
})
assert.equal(raidingRows.speed_knots.effective, 14.1)
assert.equal(raidingRows.speed_bonus_knots.modifier, 4.1)
assert.equal(raidingRows.cruising_maneuverability_pct.isDebuff, true)
assert.equal(raidingRows.cruising_speed_gain_pct.isDebuff, true)

const blueRows = statRowsByKey({ speed_pct: 6 })
assert.equal(blueRows.speed_knots.effective, 10.6)
const brightRows = statRowsByKey({ hold_capacity_pct: 12 })
assert.equal(brightRows.hold_capacity.effective, 5600)
const goldenRows = statRowsByKey({ speed_pct: 5, armor_pct: 5, damage_pct: 5 })
assert.equal(goldenRows.speed_knots.effective, 10.5)
assert.equal(goldenRows.armor.effective, 12.6)
assert.equal(goldenRows.damage_pct.modifier, 5)
const greenRows = statRowsByKey({ hull_hp_pct: 7 })
assert.equal(greenRows.durability.effective, 1070)
const lilacRows = statRowsByKey({ turn_rate_pct: 7 })
assert.equal(lilacRows.maneuverability.effective, 86)
const redRows = statRowsByKey({ turn_rate_pct: 5, damage_pct: 5, exp_loot_pct: 7 })
assert.equal(redRows.maneuverability.effective, 84)
assert.equal(redRows.damage_pct.modifier, 5)
assert.equal(redRows.exp_loot_pct.modifier, 7)
const whiteRows = statRowsByKey({ exp_loot_pct: 10 })
assert.equal(whiteRows.exp_loot_pct.modifier, 10)
const yellowRows = statRowsByKey({ damage_pct: 7 })
assert.equal(yellowRows.damage_pct.modifier, 7)


const researchAccess = calculateUpgradeSlotAccess({
  shipUpgradeSlots: 5,
  researchUpgradeSlotUnlocked: true,
})
assert.equal(researchAccess.slot5Unlocked, true)
assert.equal(researchAccess.slot6Available, false)
assert.equal(researchAccess.availableSlots, 5)

const stackedAccess = calculateUpgradeSlotAccess({
  shipUpgradeSlots: 5,
  researchUpgradeSlotUnlocked: true,
  unlockEffectSlots: 1,
})
assert.equal(stackedAccess.slot5Unlocked, true)
assert.equal(stackedAccess.slot6Available, true)
assert.equal(stackedAccess.availableSlots, 6)


const buildCreateSource = readFileSync(resolve(frontendRoot, 'src/modules/builds/pages/BuildCreatePage.vue'), 'utf8')
const indexSource = readFileSync(resolve(frontendRoot, 'index.html'), 'utf8')

assert.match(buildCreateSource, /import slotPlaceholderSrc from '@\/assets\/slot-placeholder\.svg'/)
assert.doesNotMatch(buildCreateSource, /\/icons\/slot-placeholder\.svg/)
assert.match(buildCreateSource, /<select v-model="form\.lantern"/)
assert.match(buildCreateSource, /optionsFor\('lantern'\)/)

const sailBlock = buildCreateSource.match(/equipment-slot-sail[\s\S]*?<\/label>/)?.[0] || ''
const lanternBlock = buildCreateSource.match(/equipment-slot-lantern[\s\S]*?<\/label>/)?.[0] || ''
assert.doesNotMatch(sailBlock, /slot-effect-text|formatEffects/)
assert.doesNotMatch(lanternBlock, /slot-effect-text|formatEffects/)
assert.match(buildCreateSource, /researchUpgradeEffectTotals/)
assert.match(buildCreateSource, /researchUpgradeEffectTotals\.value/)

assert.doesNotMatch(indexSource, /\/branding\/rbf-fleet-icon\.png/)
assert.match(indexSource, /\/rbf-fleet-icon\.png/)
assert.equal(existsSync(resolve(frontendRoot, 'public/rbf-fleet-icon.png')), true)
assert.equal(existsSync(resolve(frontendRoot, 'src/assets/slot-placeholder.svg')), true)

console.log('Build designer regression checks passed.')
