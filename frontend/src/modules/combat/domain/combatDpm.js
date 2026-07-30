import { percentageMultiplier } from '../../builds/buildCalculations.js'
import { roundByPrecision } from '../../builds/buildMath.js'

export const COMBAT_EFFECT_KEYS = Object.freeze({
  damage: 'damage_pct',
  reload: 'reload_pct',
  positionalDamage: 'bow_stern_weapon_damage_pct',
  lowHullDamage: 'low_hp_damage_pct',
  lowDurabilityReloadPerSailor: 'low_durability_reload_per_sailor_pct',
})

export function combatRelevantEffectKeys(effects = {}) {
  return Object.keys(effects).filter((key) => Object.values(COMBAT_EFFECT_KEYS).includes(key))
}

export function isCombatRelevantOption(option) {
  return combatRelevantEffectKeys(option?.stat_effects || {}).length > 0
}

export function buildCombatEffectSets({
  lantern = null,
  upgrades = [],
  specialists = [],
  lowDurability = false,
  sailors = 0,
} = {}) {
  const unconditional = [lantern, ...upgrades, ...specialists]
    .map((option) => option?.stat_effects || {})
    .filter((effects) => Object.keys(effects).length > 0)

  if (!lowDurability) return unconditional

  const conditional = []
  for (const option of [lantern, ...upgrades, ...specialists]) {
    const effects = option?.stat_effects || {}
    const lowHullDamage = Number(effects[COMBAT_EFFECT_KEYS.lowHullDamage] || 0)
    if (lowHullDamage) conditional.push({ damage_pct: lowHullDamage })
    const reloadPerSailor = Number(effects[COMBAT_EFFECT_KEYS.lowDurabilityReloadPerSailor] || 0)
    if (reloadPerSailor) {
      conditional.push({ reload_pct: reloadPerSailor * Math.max(0, Number(sailors) || 0) })
    }
  }
  return [...unconditional, ...conditional]
}

export function combatModifiers(effectSets = [], { positional = false } = {}) {
  const damageMultiplier = percentageMultiplier(effectSets, COMBAT_EFFECT_KEYS.damage)
    * (positional ? percentageMultiplier(effectSets, COMBAT_EFFECT_KEYS.positionalDamage) : 1)
  const reloadSpeedMultiplier = percentageMultiplier(effectSets, COMBAT_EFFECT_KEYS.reload)
  return {
    damageMultiplier,
    reloadSpeedMultiplier,
    damagePercent: (damageMultiplier - 1) * 100,
    reloadPercent: (reloadSpeedMultiplier - 1) * 100,
  }
}

function normalizeSlots(slots = []) {
  return slots
    .filter((slot) => String(slot?.item || '').trim())
    .map((slot) => ({
      item: String(slot.item).trim(),
      quantity: Math.max(1, Number(slot.quantity) || 1),
    }))
}

/**
 * Sustained armor-adjusted DPM.
 *
 * Per shot: max(0, modified damage - target armor)
 * Cycle rate: 60 / (base reload / reload-speed multiplier)
 */
export function calculateArcDpm({
  slots = [],
  optionByName,
  armor = 0,
  effectSets = [],
  positional = false,
  quantityMultiplier = 1,
} = {}) {
  const normalizedArmor = Math.max(0, Number(armor) || 0)
  const multiplier = Math.max(0, Number(quantityMultiplier) || 0)
  const modifiers = combatModifiers(effectSets, { positional })
  const missingProfiles = []
  const rows = []

  for (const slot of normalizeSlots(slots)) {
    const option = optionByName?.(slot.item)
    const profile = option?.weapon_performance
    if (!profile) {
      missingProfiles.push(slot.item)
      continue
    }
    const baseDamage = Number(profile.base_damage)
    const baseReload = Number(profile.reload_seconds)
    if (!Number.isFinite(baseDamage) || !Number.isFinite(baseReload) || baseReload <= 0) {
      missingProfiles.push(slot.item)
      continue
    }
    const effectiveDamage = baseDamage * modifiers.damageMultiplier
    const effectiveReload = baseReload / Math.max(0.0001, modifiers.reloadSpeedMultiplier)
    const damageAfterArmor = Math.max(0, effectiveDamage - normalizedArmor)
    const quantity = slot.quantity * multiplier
    const rawDpm = effectiveDamage * 60 / effectiveReload * quantity
    const armorDpm = damageAfterArmor * 60 / effectiveReload * quantity
    rows.push({
      name: slot.item,
      quantity,
      baseDamage: roundByPrecision(baseDamage, 1),
      effectiveDamage: roundByPrecision(effectiveDamage, 2),
      baseReload: roundByPrecision(baseReload, 1),
      effectiveReload: roundByPrecision(effectiveReload, 2),
      damageAfterArmor: roundByPrecision(damageAfterArmor, 2),
      rawDpm: roundByPrecision(rawDpm, 1),
      armorDpm: roundByPrecision(armorDpm, 1),
    })
  }

  return {
    complete: missingProfiles.length === 0,
    empty: rows.length === 0 && missingProfiles.length === 0,
    armor: normalizedArmor,
    rawDpm: roundByPrecision(rows.reduce((total, row) => total + Number(row.rawDpm || 0), 0), 1),
    armorDpm: roundByPrecision(rows.reduce((total, row) => total + Number(row.armorDpm || 0), 0), 1),
    damagePercent: roundByPrecision(modifiers.damagePercent, 1),
    reloadPercent: roundByPrecision(modifiers.reloadPercent, 1),
    missingProfiles: [...new Set(missingProfiles)],
    rows,
  }
}
