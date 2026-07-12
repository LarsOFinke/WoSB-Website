export const CREW_FIELDS = ['sailors', 'musketeers', 'soldiers', 'mercenaries']

function toNonNegativeInteger(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.floor(number))
}

export function crewTotal(allocation) {
  return CREW_FIELDS.reduce((total, field) => total + toNonNegativeInteger(allocation?.[field]), 0)
}

/** Return the largest value a crew row can take without exceeding capacity. */
export function crewSliderMax(allocation, field, capacity, _sailorMinimum = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const otherTotal = CREW_FIELDS
    .filter((candidate) => candidate !== field)
    .reduce((total, candidate) => total + toNonNegativeInteger(allocation?.[candidate]), 0)
  return Math.max(0, normalizedCapacity - otherTotal)
}

export function setCrewAllocationValue(allocation, field, value, capacity, sailorMinimum = 0) {
  if (!CREW_FIELDS.includes(field)) return normalizeCrewAllocation(allocation, capacity, sailorMinimum)
  const next = normalizeCrewAllocation(allocation, capacity, sailorMinimum)
  const maximum = crewSliderMax(next, field, capacity, sailorMinimum)
  next[field] = Math.min(toNonNegativeInteger(value), maximum)
  return next
}

export function normalizeCrewAllocation(allocation, capacity, _sailorMinimum = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const next = Object.fromEntries(CREW_FIELDS.map((field) => [field, toNonNegativeInteger(allocation?.[field])]))

  let overflow = Math.max(0, crewTotal(next) - normalizedCapacity)
  for (const field of ['mercenaries', 'soldiers', 'musketeers', 'sailors']) {
    if (overflow <= 0) break
    const reduction = Math.min(next[field], overflow)
    next[field] -= reduction
    overflow -= reduction
  }
  return next
}

export function sailingEfficiencyPercent(sailors, sailorMinimum) {
  const target = toNonNegativeInteger(sailorMinimum)
  if (target <= 0) return 100
  return Math.min(100, Math.max(0, Math.round((toNonNegativeInteger(sailors) / target) * 100)))
}
