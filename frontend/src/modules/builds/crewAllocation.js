export const CREW_FIELDS = ['sailors', 'musketeers', 'soldiers', 'mercenaries']

function toNonNegativeInteger(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.floor(number))
}

export function crewTotal(allocation) {
  return CREW_FIELDS.reduce((total, field) => total + toNonNegativeInteger(allocation?.[field]), 0)
}

export function crewSliderMax(allocation, field, capacity, sailorMinimum = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const normalizedMinimum = Math.min(toNonNegativeInteger(sailorMinimum), normalizedCapacity)
  const otherTotal = CREW_FIELDS
    .filter((candidate) => candidate !== field)
    .reduce((total, candidate) => total + toNonNegativeInteger(allocation?.[candidate]), 0)
  const available = Math.max(0, normalizedCapacity - otherTotal)
  return field === 'sailors' ? Math.max(normalizedMinimum, available) : available
}

export function setCrewAllocationValue(allocation, field, value, capacity, sailorMinimum = 0) {
  if (!CREW_FIELDS.includes(field)) return normalizeCrewAllocation(allocation, capacity, sailorMinimum)
  const next = normalizeCrewAllocation(allocation, capacity, sailorMinimum)
  const minimum = field === 'sailors' ? Math.min(toNonNegativeInteger(sailorMinimum), toNonNegativeInteger(capacity)) : 0
  const maximum = crewSliderMax(next, field, capacity, sailorMinimum)
  next[field] = Math.min(Math.max(toNonNegativeInteger(value), minimum), maximum)
  return next
}

export function normalizeCrewAllocation(allocation, capacity, sailorMinimum = 0) {
  const normalizedCapacity = toNonNegativeInteger(capacity)
  const normalizedMinimum = Math.min(toNonNegativeInteger(sailorMinimum), normalizedCapacity)
  const next = Object.fromEntries(CREW_FIELDS.map((field) => [field, toNonNegativeInteger(allocation?.[field])]))

  next.sailors = Math.max(next.sailors, normalizedMinimum)

  let overflow = Math.max(0, crewTotal(next) - normalizedCapacity)
  // Reduce optional crew first. Sailors are only reduced down to the effective minimum.
  for (const field of ['mercenaries', 'soldiers', 'musketeers']) {
    if (overflow <= 0) break
    const reduction = Math.min(next[field], overflow)
    next[field] -= reduction
    overflow -= reduction
  }
  if (overflow > 0) {
    const reducibleSailors = Math.max(0, next.sailors - normalizedMinimum)
    const reduction = Math.min(reducibleSailors, overflow)
    next.sailors -= reduction
    overflow -= reduction
  }

  // A malformed persisted allocation can still exceed capacity when the minimum
  // itself was larger than the capacity. The minimum is clamped above, so this
  // final guard keeps the result deterministic.
  if (crewTotal(next) > normalizedCapacity) {
    next.sailors = normalizedCapacity
    next.musketeers = 0
    next.soldiers = 0
    next.mercenaries = 0
  }

  return next
}
