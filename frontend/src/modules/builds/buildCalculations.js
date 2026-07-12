export function sumEffects(...effectSets) {
  const totals = {}
  for (const effects of effectSets) {
    for (const [key, rawValue] of Object.entries(effects || {})) {
      totals[key] = (Number(totals[key]) || 0) + (Number(rawValue) || 0)
    }
  }
  return totals
}

export function calculateUpgradeSlotAccess({
  shipUpgradeSlots,
  unlockEffectSlots = 0,
  researchUpgradeSlotUnlocked = false,
  slotLimit = 7,
  baseSlotLimit = 4,
  standardShipSlots = 5,
}) {
  const configuredSlots = Math.max(Number(shipUpgradeSlots) || 0, 0)
  const baseSlots = Math.min(configuredSlots, baseSlotLimit)
  const effectSlots = Math.min(Math.max(Number(unlockEffectSlots) || 0, 0), slotLimit - baseSlots)
  const researchSlots = researchUpgradeSlotUnlocked ? 1 : 0
  const shipExtraSlots = Math.min(
    Math.max(configuredSlots - standardShipSlots, 0),
    slotLimit - baseSlots,
  )
  const availableSlots = Math.min(
    slotLimit,
    baseSlots + researchSlots + effectSlots + shipExtraSlots,
  )

  return {
    baseSlots,
    effectSlots,
    researchSlots,
    shipExtraSlots,
    slot5Unlocked: availableSlots >= 5,
    slot6Available: availableSlots >= 6,
    slot7Available: availableSlots >= 7,
    availableSlots,
  }
}

export function calculateBuildUpgradeSlotAccess({
  form,
  shipUpgradeSlots,
  effectForUpgrade,
  slotLimit = 7,
}) {
  const selectedUpgradeNames = Array.from(
    { length: slotLimit },
    (_, offset) => form?.[`upgrade_${offset + 1}`] || '',
  )
  const researchUpgradeSlotUnlocked = Boolean(form?.research_upgrade_slot_unlocked)
  const preExpansionAccess = calculateUpgradeSlotAccess({
    shipUpgradeSlots,
    researchUpgradeSlotUnlocked,
    slotLimit,
  })
  const expansionUnlockSlots = selectedUpgradeNames
    .slice(0, preExpansionAccess.availableSlots)
    .filter(Boolean)
    .reduce((total, name) => {
      const grossSlots = Math.max(0, Number(effectForUpgrade?.(name)?.extra_upgrade_slots) || 0)
      return total + (grossSlots > 0 ? Math.max(grossSlots - 1, 0) : 0)
    }, 0)
  return {
    ...calculateUpgradeSlotAccess({
      shipUpgradeSlots,
      unlockEffectSlots: expansionUnlockSlots,
      researchUpgradeSlotUnlocked,
      slotLimit,
    }),
    selectedUpgradeNames,
    expansionUnlockSlots,
  }
}

function numberOrNull(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  return Number(value)
}

function roundByPrecision(value, precision = 0) {
  const number = numberOrNull(value)
  if (number === null) return null
  const factor = 10 ** Number(precision || 0)
  const rounded = Math.round(number * factor) / factor
  return Number(precision || 0) === 0 ? Math.round(rounded) : rounded
}

/**
 * Calculate the live Build Designer stat rows from the exact same catalog
 * contract used by the backend: a ship base field plus percentage and/or flat
 * effect keys supplied by the selected catalog options.
 */
export function calculateBuildStatRows({ ship, definitions = [], effects = {} }) {
  if (!ship) return []

  return definitions
    .map((definition) => {
      const base = definition?.base_field ? numberOrNull(ship[definition.base_field]) : null
      const pctModifier = Number(effects[definition?.pct_effect] || 0)
      const flatModifier = Number(effects[definition?.flat_effect] || 0)
      const modifier = pctModifier + flatModifier
      if (base === null && modifier === 0) return null

      let effective = base
      if (effective !== null && definition.pct_effect) {
        effective *= (1 + pctModifier / 100)
      }
      const calculationFlatModifier = Number(effects[definition.calculation_flat_effect] || 0)
      if (effective !== null && definition.calculation_flat_effect) {
        effective += calculationFlatModifier
      } else if (effective !== null && definition.flat_effect) {
        effective += flatModifier
      }
      if (effective === null && definition.flat_effect) {
        effective = flatModifier
      }

      return {
        ...definition,
        base: roundByPrecision(base, definition.precision),
        modifier: roundByPrecision(modifier, definition.precision),
        effective: roundByPrecision(effective, definition.precision),
        modifier_kind: definition.pct_effect && definition.base_field ? 'percent' : 'flat',
        effect_key: definition.pct_effect || definition.flat_effect,
        isDebuff: modifier !== 0
          && (definition.positive_is_good === false ? modifier > 0 : modifier < 0),
      }
    })
    .filter(Boolean)
}
