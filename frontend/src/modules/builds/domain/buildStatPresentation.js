import { roundByPrecision } from '../buildMath.js'

export const CORE_BUILD_STAT_KEYS = new Set([
  'durability',
  'speed_min_knots',
  'speed_knots',
  'maneuverability',
  'armor',
  'hold_capacity',
  'crew_capacity',
  'sailor_minimum',
  'displacement_tons',
])

const DUPLICATE_COMPONENT_KEYS = new Set([
  'durability_bonus',
  'speed_bonus_knots',
  'maneuverability_bonus',
  'armor_bonus',
  'hold_capacity_bonus',
  'crew_capacity_bonus',
])

export { roundByPrecision } from '../buildMath.js'

export function formatStatValue(value, unit, precision = 0) {
  const number = roundByPrecision(value, precision)
  if (number === null) return '—'
  return `${number}${unit ? ` ${unit}` : ''}`
}

function signedValue(value, precision, suffix = '') {
  const number = Number(value || 0)
  if (!Number.isFinite(number) || number === 0) return ''
  return `${number > 0 ? '+' : ''}${roundByPrecision(number, precision)}${suffix}`
}

export function formatBuildModifier(row) {
  if (String(row?.effect_key || row?.key || '').endsWith('_enabled')) return '✓'

  const percent = Number(row?.percent_modifier || 0)
  const flat = Number(row?.flat_modifier || 0)
  const parts = []
  if (percent) parts.push(signedValue(percent, 1, '%'))
  if (flat) {
    const suffix = row?.unit ? ` ${row.unit}` : ''
    parts.push(signedValue(flat, row?.precision || 0, suffix))
  }
  if (parts.length) return parts.join(' · ')

  // Backward compatibility for saved/API responses created before modifier
  // components were added.
  const value = Number(row?.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const suffix = row?.modifier_kind === 'percent'
    || row?.unit === '%'
    || String(row?.effect_key || '').endsWith('_pct')
    ? '%'
    : (row?.unit ? ` ${row.unit}` : '')
  return signedValue(value, row?.precision || 0, suffix)
}

export function rowIsDebuff(row) {
  return Boolean(row?.isDebuff ?? row?.is_debuff)
}

export function isActiveBuildEffect(row) {
  if (!Number(row?.modifier || 0)) return false
  if (row?.key === 'speed_min_knots') return false
  return !DUPLICATE_COMPONENT_KEYS.has(row?.key)
}
