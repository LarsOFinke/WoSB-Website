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

import { calculateUpgradeSlotAccess, sumEffects } from '../src/modules/builds/buildCalculations.js'

assert.deepEqual(sumEffects({ speed_pct: 4 }, { speed_pct: 3, reload_pct: 2 }), {
  speed_pct: 7,
  reload_pct: 2,
})

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
