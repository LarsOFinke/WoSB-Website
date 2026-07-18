import { emptyInventorySlot, normalizeInventorySlots } from '../inventorySlots.js'

export const GINGER_SPECIALIST_NAME = 'Ginger'
export const REGULAR_SPECIALIST_LIMIT = 4

export function splitSpecialistSelection(slots) {
  const normalized = normalizeInventorySlots(slots)
  return {
    gingerSelected: normalized.some((slot) => slot.item === GINGER_SPECIALIST_NAME),
    regular: normalized.filter((slot) => slot.item !== GINGER_SPECIALIST_NAME).slice(0, REGULAR_SPECIALIST_LIMIT),
  }
}

export function composeSpecialistSelection(regular, gingerSelected, includeEmptyRow = true) {
  const normalizedRegular = normalizeInventorySlots(regular)
    .filter((slot) => slot.item !== GINGER_SPECIALIST_NAME)
    .slice(0, REGULAR_SPECIALIST_LIMIT)
    .map((slot) => ({ ...slot, quantity: 1 }))
  const selected = gingerSelected
    ? [...normalizedRegular, { item: GINGER_SPECIALIST_NAME, quantity: 1 }]
    : normalizedRegular
  return includeEmptyRow && normalizedRegular.length < REGULAR_SPECIALIST_LIMIT
    ? [...selected, emptyInventorySlot()]
    : selected
}
