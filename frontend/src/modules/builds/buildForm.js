import { emptyInventorySlot } from '@/modules/builds/inventorySlots'

export const equipmentUpgradeCount = 7

export const weaponArcFields = Object.freeze([
  { fieldName: 'front_weapon_slots', labelKey: 'builds.create.weapons.front', altKey: 'builds.create.weapons.frontAlt' },
  { fieldName: 'rear_weapon_slots', labelKey: 'builds.create.weapons.rear', altKey: 'builds.create.weapons.rearAlt' },
  { fieldName: 'port_weapon_slots', labelKey: 'builds.create.weapons.port', altKey: 'builds.create.weapons.portAlt' },
  { fieldName: 'starboard_weapon_slots', labelKey: 'builds.create.weapons.starboard', altKey: 'builds.create.weapons.starboardAlt' },
  { fieldName: 'mortar_weapon_slots', labelKey: 'builds.create.weapons.mortar', altKey: 'builds.create.weapons.mortarAlt' },
  { fieldName: 'special_weapon_slots', labelKey: 'builds.create.weapons.special', altKey: 'builds.create.weapons.specialAlt' },
])

export const slotLimits = Object.freeze({
  front_weapon_slots: 12,
  rear_weapon_slots: 12,
  port_weapon_slots: 12,
  starboard_weapon_slots: 12,
  mortar_weapon_slots: 8,
  special_weapon_slots: 8,
  special_crew_slots: 8,
  ammunition_slots: 12,
  consumable_slots: 3,
  hold_slots: 24,
})

export function createBuildForm() {
  return {
    build_name: '',
    build_type: 'balanced',
    ship_id: '',
    sails: '',
    upgrade_1: '',
    upgrade_2: '',
    upgrade_3: '',
    upgrade_4: '',
    upgrade_5: '',
    upgrade_6: '',
    upgrade_7: '',
    lantern: '',
    research_upgrade_slot_unlocked: false,
    sailors: 0,
    soldiers: 0,
    musketeers: 0,
    mercenaries: 0,
    front_weapon_slots: [emptyInventorySlot()],
    rear_weapon_slots: [emptyInventorySlot()],
    port_weapon_slots: [emptyInventorySlot()],
    starboard_weapon_slots: [emptyInventorySlot()],
    mortar_weapon_slots: [emptyInventorySlot()],
    special_weapon_slots: [emptyInventorySlot()],
    special_crew_slots: [emptyInventorySlot()],
    ammunition_slots: [emptyInventorySlot()],
    consumable_slots: [emptyInventorySlot()],
    hold_slots: [emptyInventorySlot()],
    details: '',
  }
}

export function sortShipsForDropdown(shipRows) {
  return [...shipRows].sort((left, right) => {
    const rateDiff = Number(right.rate || 0) - Number(left.rate || 0)
    if (rateDiff !== 0) return rateDiff
    return String(left.name || '').localeCompare(String(right.name || ''), undefined, { sensitivity: 'base' })
  })
}
