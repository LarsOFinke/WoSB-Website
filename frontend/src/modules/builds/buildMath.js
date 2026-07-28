function numberOrNull(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  return Number(value)
}

/**
 * Round decimal build values identically to Python Decimal ROUND_HALF_UP.
 *
 * JavaScript's native Math.round differs for negative ties, while Python's
 * built-in round uses bankers' rounding. Build previews, validation and API
 * responses therefore share this explicit half-away-from-zero contract.
 */
export function roundByPrecision(value, precision = 0) {
  const number = numberOrNull(value)
  if (number === null) return null
  const digits = Math.max(0, Number(precision || 0))
  const factor = 10 ** digits
  const roundedMagnitude = Math.round((Math.abs(number) * factor) + Number.EPSILON) / factor
  const rounded = Math.sign(number) * roundedMagnitude
  return digits === 0 ? Math.trunc(rounded) : rounded
}
