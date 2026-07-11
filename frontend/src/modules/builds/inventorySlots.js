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

export function inventoryQuantityTotal(slots, excludeIndex = null) {
  if (!Array.isArray(slots)) return 0
  return slots.reduce((total, slot, index) => {
    if (index === excludeIndex || !String(slot?.item || '').trim()) return total
    return total + Math.max(1, Number(slot?.quantity) || 1)
  }, 0)
}

export function remainingInventoryQuantity(slots, index, maxTotalQuantity) {
  const capacity = Math.max(0, Number(maxTotalQuantity) || 0)
  if (!capacity) return 0
  return Math.max(0, capacity - inventoryQuantityTotal(slots, index))
}

export function reconcileInventorySlots(
  slots,
  maxSlots,
  { isItemAllowed = () => true, maxTotalQuantity = null } = {},
) {
  const limit = Math.max(0, Number(maxSlots) || 0)
  if (limit === 0) return []

  const quantityLimit = maxTotalQuantity !== null
    && maxTotalQuantity !== undefined
    && Number.isFinite(Number(maxTotalQuantity))
    ? Math.max(0, Number(maxTotalQuantity))
    : null
  let remainingQuantity = quantityLimit
  const filled = []

  for (const slot of normalizeInventorySlots(slots)) {
    if (filled.length >= limit || !isItemAllowed(slot.item)) continue
    if (remainingQuantity !== null && remainingQuantity <= 0) break

    const quantity = remainingQuantity === null
      ? slot.quantity
      : Math.min(slot.quantity, remainingQuantity)
    filled.push({ ...slot, quantity })
    if (remainingQuantity !== null) remainingQuantity -= quantity
  }

  const hasQuantityCapacity = remainingQuantity === null || remainingQuantity > 0
  if (filled.length < limit && hasQuantityCapacity) filled.push(emptyInventorySlot())
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
  const remaining = options.maxTotalQuantity !== null
    && options.maxTotalQuantity !== undefined
    && Number.isFinite(Number(options.maxTotalQuantity))
    ? remainingInventoryQuantity(next, index, options.maxTotalQuantity)
    : null
  const normalizedQuantity = Math.max(1, Number(quantity) || 1)
  next[index].quantity = remaining === null ? normalizedQuantity : Math.min(normalizedQuantity, Math.max(1, remaining))
  return reconcileInventorySlots(next, maxSlots, options)
}
