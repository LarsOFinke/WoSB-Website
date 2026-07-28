import { roundByPrecision } from './buildMath.js'

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
  slotLimit = 8,
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
    slot8Available: availableSlots >= 8,
    availableSlots,
  }
}

export function calculateBuildUpgradeSlotAccess({
  form,
  shipUpgradeSlots,
  effectForUpgrade,
  slotLimit = 8,
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
      return total + grossSlots
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

export function percentageMultiplier(effectSets, effectKey, fallbackTotal = 0) {
  const values = (effectSets || [])
    .map((effects) => Number(effects?.[effectKey] || 0))
    .filter((value) => Number.isFinite(value) && value !== 0)
  if (!values.length) return 1 + Number(fallbackTotal || 0) / 100
  return values.reduce((multiplier, value) => multiplier * (1 + value / 100), 1)
}

export function applyPercentageEffects(baseValue, effectKey, effectSets, fallbackTotal = 0) {
  return Number(baseValue || 0) * percentageMultiplier(effectSets, effectKey, fallbackTotal)
}

function numberOrNull(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  return Number(value)
}

export { roundByPrecision } from './buildMath.js'

/**
 * Calculate the live Build Designer stat rows from the exact same catalog
 * contract used by the backend: a ship base field plus percentage and/or flat
 * effect keys supplied by the selected catalog options.
 */
export function calculateBuildStatRows({ ship, definitions = [], effects = {}, effectSets = [] }) {
  if (!ship) return []

  return definitions
    .map((definition) => {
      const base = definition?.base_field ? numberOrNull(ship[definition.base_field]) : null
      const pctMultiplier = definition?.pct_effect
        ? percentageMultiplier(effectSets, definition.pct_effect, Number(effects[definition.pct_effect] || 0))
        : 1
      const percentModifier = definition?.pct_effect ? (pctMultiplier - 1) * 100 : 0
      const flatEffectKey = definition?.calculation_flat_effect || definition?.flat_effect
      const flatModifier = flatEffectKey ? Number(effects[flatEffectKey] || 0) : 0
      if (base === null && percentModifier === 0 && flatModifier === 0) return null

      let effective = base
      if (effective !== null && definition.pct_effect) {
        const configuredPctBase = definition.pct_base_field
          ? numberOrNull(ship[definition.pct_base_field])
          : base
        const pctBase = configuredPctBase === null || (configuredPctBase <= 0 && base > 0)
          ? base
          : configuredPctBase
        effective = base + (pctBase * percentModifier / 100)
      }
      if (effective !== null) {
        effective += flatModifier
      } else if (definition.flat_effect) {
        effective = flatModifier
      }

      const rawModifier = base !== null && effective !== null
        ? effective - base
        : (flatModifier || percentModifier)
      const hasPercentage = percentModifier !== 0
      const hasFlat = flatModifier !== 0
      const modifierKind = hasPercentage && hasFlat
        ? 'composite'
        : hasPercentage
          ? 'percent'
          : 'flat'
      const delta = base !== null && effective !== null ? effective - base : rawModifier
      const isDebuff = delta !== 0
        && (definition.positive_is_good === false ? delta > 0 : delta < 0)

      return {
        ...definition,
        base: roundByPrecision(base, definition.precision),
        modifier: roundByPrecision(rawModifier, definition.precision),
        percent_modifier: hasPercentage ? roundByPrecision(percentModifier, 1) : null,
        flat_modifier: hasFlat ? roundByPrecision(flatModifier, definition.precision) : null,
        effective: roundByPrecision(effective, definition.precision),
        modifier_kind: modifierKind,
        effect_key: definition.pct_effect || definition.flat_effect,
        isDebuff,
      }
    })
    .filter(Boolean)
}
