import { slotLimits } from '@/modules/builds/buildForm'
import { emptyInventorySlot, normalizeInventorySlots } from '@/modules/builds/inventorySlots'

const SCALAR_FIELDS = [
  'build_name', 'build_type', 'ship_id', 'sails', 'upgrade_1', 'upgrade_2', 'upgrade_3',
  'upgrade_4', 'upgrade_5', 'upgrade_6', 'upgrade_7', 'upgrade_8', 'lantern',
  'research_upgrade_slot_unlocked', 'sailors', 'soldiers', 'musketeers', 'mercenaries', 'details',
]

export function resetBuildSlots(form, slotLimitForField) {
  for (const fieldName of Object.keys(slotLimits)) {
    form[fieldName] = slotLimitForField(fieldName) > 0 ? [emptyInventorySlot()] : []
  }
}

export function hydrateBuildForm(form, build, slotLimitForField) {
  for (const fieldName of SCALAR_FIELDS) {
    form[fieldName] = build[fieldName] ?? form[fieldName]
  }
  for (const fieldName of Object.keys(slotLimits)) {
    const slots = Array.isArray(build[fieldName]) ? build[fieldName].map((slot) => ({ ...slot })) : []
    form[fieldName] = slots.length
      ? slots
      : (slotLimitForField(fieldName) > 0 ? [emptyInventorySlot()] : [])
  }
}

export function createBuildPayload(form) {
  return {
    ...form,
    ship_id: Number(form.ship_id),
    sailors: Number(form.sailors),
    soldiers: Number(form.soldiers),
    musketeers: Number(form.musketeers),
    mercenaries: Number(form.mercenaries),
    front_weapon_slots: normalizeInventorySlots(form.front_weapon_slots),
    rear_weapon_slots: normalizeInventorySlots(form.rear_weapon_slots),
    port_weapon_slots: normalizeInventorySlots(form.port_weapon_slots),
    starboard_weapon_slots: normalizeInventorySlots(form.starboard_weapon_slots),
    mortar_weapon_slots: normalizeInventorySlots(form.mortar_weapon_slots),
    special_weapon_slots: normalizeInventorySlots(form.special_weapon_slots),
    special_crew_slots: normalizeInventorySlots(form.special_crew_slots)
      .map((slot) => ({ ...slot, quantity: 1 })),
    ammunition_slots: normalizeInventorySlots(form.ammunition_slots),
    consumable_slots: normalizeInventorySlots(form.consumable_slots),
    hold_slots: normalizeInventorySlots(form.hold_slots),
  }
}
