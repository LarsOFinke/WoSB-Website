const REGULAR_WEAPON_SLOT_TYPES = new Set([
  'weapon_front',
  'weapon_rear',
  'weapon_port',
  'weapon_starboard',
])

export function rateWeaponClass(rules = [], rate) {
  return rules.find((row) => Number(row.rate) === Number(rate))?.weapon_class || ''
}

export function applyRateWeaponClassDefaults(
  mounts = [],
  rules = [],
  rate,
  { previousRate = null, force = false } = {},
) {
  const nextClass = rateWeaponClass(rules, rate)
  if (!nextClass) return mounts
  const previousClass = rateWeaponClass(rules, previousRate)

  for (const mount of mounts) {
    if (!REGULAR_WEAPON_SLOT_TYPES.has(mount.slot_type)) continue
    if (force || !mount.max_weapon_class || mount.max_weapon_class === previousClass) {
      mount.max_weapon_class = nextClass
    }
  }
  return mounts
}
