export const CREW_FIELDS = ['sailors', 'musketeers', 'soldiers', 'mercenaries']

function toNonNegativeInteger(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.floor(number))
}

export function crewTotal(allocation) {
  return CREW_FIELDS.reduce((total, field) => total + toNonNegativeInteger(allocation?.[field]), 0)
}

/**
 * Return the largest value the selected crew row can take without exceeding
 * total ship capacity. Sailors have an additional in-game cap: the ship's
 * sailing-crew target (the value shown as `0 / N` in the crew screen). It is a
 * target for 100% working speed, not a mandatory minimum.
 */
export function crewSliderMax(allocation, field, capacity, sailorTarget = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const normalizedTarget = Math.min(toNonNegativeInteger(sailorTarget), normalizedCapacity)
  const otherTotal = CREW_FIELDS
    .filter((candidate) => candidate !== field)
    .reduce((total, candidate) => total + toNonNegativeInteger(allocation?.[candidate]), 0)
  const available = Math.max(0, normalizedCapacity - otherTotal)
  return field === 'sailors' && normalizedTarget > 0
    ? Math.min(normalizedTarget, available)
    : available
}

export function setCrewAllocationValue(allocation, field, value, capacity, sailorTarget = 0) {
  if (!CREW_FIELDS.includes(field)) return normalizeCrewAllocation(allocation, capacity, sailorTarget)
  const next = normalizeCrewAllocation(allocation, capacity, sailorTarget)
  const maximum = crewSliderMax(next, field, capacity, sailorTarget)
  next[field] = Math.min(toNonNegativeInteger(value), maximum)
  return next
}

export function normalizeCrewAllocation(allocation, capacity, sailorTarget = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const normalizedTarget = Math.min(toNonNegativeInteger(sailorTarget), normalizedCapacity)
  const next = Object.fromEntries(CREW_FIELDS.map((field) => [field, toNonNegativeInteger(allocation?.[field])]))

  if (normalizedTarget > 0) next.sailors = Math.min(next.sailors, normalizedTarget)

  let overflow = Math.max(0, crewTotal(next) - normalizedCapacity)
  // Reduce the rows that were added last in the UI first, then sailors. No row
  // is mandatory: a ship with fewer sailors remains a valid build and simply
  // has a lower sailing working-speed percentage.
  for (const field of ['mercenaries', 'soldiers', 'musketeers', 'sailors']) {
    if (overflow <= 0) break
    const reduction = Math.min(next[field], overflow)
    next[field] -= reduction
    overflow -= reduction
  }

  return next
}

export function sailingEfficiencyPercent(sailors, sailorTarget) {
  const target = toNonNegativeInteger(sailorTarget)
  if (target <= 0) return 100
  return Math.min(100, Math.max(0, Math.round((toNonNegativeInteger(sailors) / target) * 100)))
}
