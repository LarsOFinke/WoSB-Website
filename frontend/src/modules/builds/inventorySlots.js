const WEAPON_INVENTORY_FIELDS = new Set([
  'front_weapon_slots',
  'rear_weapon_slots',
  'port_weapon_slots',
  'starboard_weapon_slots',
  'mortar_weapon_slots',
  'special_weapon_slots',
])

export function isWeaponInventoryField(fieldName) {
  return WEAPON_INVENTORY_FIELDS.has(fieldName)
}

export function emptyInventorySlot() {
  return { item: '', quantity: 1 }
}

export function normalizeInventorySlots(slots) {
  if (!Array.isArray(slots)) return []
  return slots
    .map((slot) => ({
      item: String(slot?.item || '').trim(),
      quantity: Math.max(1, Number(slot?.quantity) || 1),
    }))
    .filter((slot) => slot.item)
}

export function reconcileInventorySlots(slots, maxSlots, { isItemAllowed = () => true } = {}) {
  const limit = Math.max(0, Number(maxSlots) || 0)
  if (limit === 0) return []

  const filled = normalizeInventorySlots(slots)
    .filter((slot) => isItemAllowed(slot.item))
    .slice(0, limit)

  if (filled.length < limit) filled.push(emptyInventorySlot())
  return filled
}

export function selectInventoryItem(slots, index, item, maxSlots, options = {}) {
  const next = Array.isArray(slots) ? slots.map((slot) => ({ ...slot })) : []
  while (next.length <= index) next.push(emptyInventorySlot())
  next[index].item = String(item || '')
  return reconcileInventorySlots(next, maxSlots, options)
}

export function setInventoryQuantity(slots, index, quantity, maxSlots, options = {}) {
  const next = Array.isArray(slots) ? slots.map((slot) => ({ ...slot })) : []
  while (next.length <= index) next.push(emptyInventorySlot())
  next[index].quantity = Math.max(1, Number(quantity) || 1)
  return reconcileInventorySlots(next, maxSlots, options)
}
