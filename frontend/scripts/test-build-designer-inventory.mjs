import assert from 'node:assert/strict'

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

console.log('Build designer inventory slot regression checks passed.')

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
