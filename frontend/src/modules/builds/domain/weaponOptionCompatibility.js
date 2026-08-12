const MORTAR_OPTION_KINDS = new Set(['mortar', 'mortar_launcher', 'mortar_universal'])

export function isMortarOptionKind(kind) {
  return MORTAR_OPTION_KINDS.has(kind)
}

export function isMortarOptionCompatible(option, maximumCaliber) {
  if (!isMortarOptionKind(option?.option_kind)) return false
  if (['mortar_launcher', 'mortar_universal'].includes(option.option_kind)) return true
  const caliber = Number(option.weapon_caliber_inches)
  const maximum = Number(maximumCaliber)
  return !Number.isFinite(caliber) || Number.isFinite(maximum) && caliber <= maximum
}
