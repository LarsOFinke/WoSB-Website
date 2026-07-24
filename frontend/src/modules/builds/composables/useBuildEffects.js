import { computed } from 'vue'

import { applyPercentageEffects, calculateBuildStatRows, calculateBuildUpgradeSlotAccess, sumEffects } from '@/modules/builds/buildCalculations'
import { equipmentUpgradeCount } from '@/modules/builds/buildForm'
import { normalizeInventorySlots } from '@/modules/builds/inventorySlots'
import { calculateSpecialistEffectSets } from '@/modules/builds/specialistEffects'
import { sailingEfficiencyPercent } from '@/modules/builds/crewAllocation'
import { splitSpecialistSelection } from '@/modules/builds/domain/specialistSelection'

const UPGRADE_GROUP_ORDER = ['speed', 'expeditionary', 'protection', 'combat', 'unusual', 'mortar', 'other']

export function useBuildEffects({
  form,
  optionCatalog,
  selectedShip,
  optionLabel,
  t,
  catalog,
  inventory,
  saving,
}) {
  const baseCrewCapacity = computed(() => selectedShip.value?.crew_capacity || 0)
  const baseSailorMinimum = computed(() => selectedShip.value?.sailor_minimum || 0)
  const upgradeAccess = computed(() => calculateBuildUpgradeSlotAccess({
    form,
    shipUpgradeSlots: selectedShip.value?.upgrade_slots || 0,
    effectForUpgrade: catalog.upgradeEffects,
    slotLimit: equipmentUpgradeCount,
  }))
  const selectedUpgradeNames = computed(() => upgradeAccess.value.selectedUpgradeNames)
  const upgradeEffectTotals = computed(() => sumEffects(
    ...selectedUpgradeNames.value.filter(Boolean).map(catalog.upgradeEffects),
  ))
  const specialCrewEffectSets = computed(() => calculateSpecialistEffectSets({
    slots: normalizeInventorySlots(form.special_crew_slots),
    effectForItem: catalog.specialCrewEffects,
    crew: {
      sailors: form.sailors,
      soldiers: form.soldiers,
      musketeers: form.musketeers,
      mercenaries: form.mercenaries,
    },
  }))
  const specialCrewEffectTotals = computed(() => sumEffects(...specialCrewEffectSets.value))
  const equipmentEffectTotals = computed(() => sumEffects(
    catalog.optionEffects('sail', form.sails),
    catalog.optionEffects('lantern', form.lantern),
  ))
  const researchUpgradeEffectTotals = computed(() => form.research_upgrade_slot_unlocked
    ? optionCatalog.value.research_upgrade_slot_effects || {}
    : {})
  const mortarModificationEffectTotals = computed(() => {
    const modification = form.mortar_modification_installed
      ? selectedShip.value?.mortar_modification
      : null
    if (!modification) return {}
    return {
      durability: Number(modification.durability_delta) || 0,
      speed_pct: Number(modification.speed_pct) || 0,
      maneuverability: Number(modification.maneuverability_delta) || 0,
      hold_capacity_pct: Number(modification.hold_capacity_pct) || 0,
      crew_capacity: Number(modification.crew_capacity_delta) || 0,
    }
  })
  const buildEffectTotals = computed(() => sumEffects(
    mortarModificationEffectTotals.value,
    equipmentEffectTotals.value,
    upgradeEffectTotals.value,
    specialCrewEffectTotals.value,
    researchUpgradeEffectTotals.value,
  ))
  const buildEffectSets = computed(() => [
    mortarModificationEffectTotals.value,
    catalog.optionEffects('sail', form.sails),
    catalog.optionEffects('lantern', form.lantern),
    ...selectedUpgradeNames.value.filter(Boolean).map(catalog.upgradeEffects),
    ...specialCrewEffectSets.value,
    researchUpgradeEffectTotals.value,
  ].filter((effects) => Object.keys(effects || {}).length > 0))

  const upgradeSlot5Unlocked = computed(() => upgradeAccess.value.slot5Unlocked)
  const upgradeSlot6Available = computed(() => upgradeAccess.value.slot6Available)
  const upgradeSlot7Available = computed(() => upgradeAccess.value.slot7Available)
  const upgradeSlot8Available = computed(() => upgradeAccess.value.slot8Available)
  const availableUpgradeSlots = computed(() => upgradeAccess.value.availableSlots)
  const crewCapacity = computed(() => Math.max(0, Math.round(
    applyPercentageEffects(
      baseCrewCapacity.value,
      'crew_capacity_pct',
      buildEffectSets.value,
      Number(buildEffectTotals.value.crew_capacity_pct) || 0,
    ) + (Number(buildEffectTotals.value.crew_capacity) || 0),
  )))
  const sailorMinimum = computed(() => Math.max(
    0,
    baseSailorMinimum.value + (Number(buildEffectTotals.value.sailor_minimum) || 0),
  ))
  const sailingEfficiency = computed(() => sailingEfficiencyPercent(form.sailors, sailorMinimum.value))
  const crewTotal = computed(() => ['sailors', 'soldiers', 'musketeers', 'mercenaries']
    .reduce((total, field) => total + Number(form[field]), 0))
  const crewRemaining = computed(() => Math.max(0, crewCapacity.value - crewTotal.value))
  const crewOverLimit = computed(() => crewCapacity.value > 0 && crewTotal.value > crewCapacity.value)
  const sailorsBelowMinimum = computed(() => Boolean(selectedShip.value) && Number(form.sailors) < sailorMinimum.value)
  const crewInvalid = computed(() => crewOverLimit.value || sailorsBelowMinimum.value)
  const specialCrewLimit = computed(() => Math.max(
    1,
    Number(optionCatalog.value.limits?.special_crew_regular_limit || optionCatalog.value.limits?.special_crew_total) || 4,
  ))
  const regularSpecialCrewCount = computed(() => splitSpecialistSelection(form.special_crew_slots).regular.length)
  const specialCrewOverCapacity = computed(() => regularSpecialCrewCount.value > specialCrewLimit.value)
  const upgradeSlotsUsed = computed(() => selectedUpgradeNames.value.filter(Boolean).length)
  const shipStatsPreview = computed(() => ({
    weaponTotal: inventory.allWeaponQuantityTotal(),
    specialCrew: inventory.slotCount('special_crew_slots'),
    inventorySlots: ['ammunition_slots', 'consumable_slots', 'hold_slots']
      .reduce((total, field) => total + inventory.slotCount(field), 0),
    upgrades: upgradeSlotsUsed.value,
  }))
  const buildStatRows = computed(() => calculateBuildStatRows({
    ship: selectedShip.value,
    definitions: optionCatalog.value.stat_definitions || [],
    effects: buildEffectTotals.value,
    effectSets: buildEffectSets.value,
  }).map((row) => {
    const path = `builds.statLabels.${row.key}`
    const translated = t(path)
    return {
      ...row,
      label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated,
    }
  }))

  function isUpgradeSlotDisabled(index) {
    if (index === 5) return !upgradeSlot5Unlocked.value
    if (index === 6) return !upgradeSlot6Available.value
    if (index === 7) return !upgradeSlot7Available.value
    if (index === 8) return !upgradeSlot8Available.value
    return false
  }

  function upgradeSlotPlaceholder(index) {
    if (index === 5 && !upgradeSlot5Unlocked.value) return t('builds.create.equipment.lockedUpgrade5')
    if (index === 6 && !upgradeSlot6Available.value) return t('builds.create.equipment.lockedUpgrade6')
    if (index === 7 && !upgradeSlot7Available.value) return t('builds.create.equipment.lockedUpgrade7')
    if (index === 8 && !upgradeSlot8Available.value) return t('builds.create.equipment.lockedUpgrade8')
    return t('common.empty')
  }

  const selectedUpgradeCards = computed(() => Array.from({ length: equipmentUpgradeCount }, (_, offset) => {
    const index = offset + 1
    const name = form[`upgrade_${index}`]
    return {
      index,
      name,
      label: name ? optionLabel(name) : '',
      effects: name ? catalog.formatEffects(name) : '',
      locked: isUpgradeSlotDisabled(index),
    }
  }))
  const activeEffectRows = computed(() => buildStatRows.value.filter((row) => Number(row.modifier || 0) !== 0))

  function upgradeOptionsForSlot(index) {
    const current = form[`upgrade_${index}`]
    const selectedElsewhere = new Set(Array.from({ length: equipmentUpgradeCount }, (_, offset) => offset + 1)
      .filter((slotIndex) => slotIndex !== index)
      .map((slotIndex) => form[`upgrade_${slotIndex}`])
      .filter(Boolean))
    return catalog.optionsFor('upgrade').filter((option) => option === current || !selectedElsewhere.has(option))
  }

  function upgradeGroupsForSlot(index) {
    const grouped = new Map()
    for (const option of upgradeOptionsForSlot(index)) {
      const kind = String(catalog.optionMeta('upgrade', option)?.option_kind || '')
      const group = kind.startsWith('ship_upgrade_') ? kind.slice('ship_upgrade_'.length) : 'other'
      if (!grouped.has(group)) grouped.set(group, [])
      grouped.get(group).push(option)
    }
    return UPGRADE_GROUP_ORDER.filter((group) => grouped.has(group)).map((group) => ({
      key: group,
      label: t(`builds.upgradeGroups.${group}`),
      options: grouped.get(group),
    }))
  }

  const submitBlockers = computed(() => {
    const blockers = []
    if (!form.build_name.trim()) blockers.push(t('builds.create.saveReadiness.reasons.name'))
    if (!form.ship_id) blockers.push(t('builds.create.saveReadiness.reasons.ship'))
    if (sailorsBelowMinimum.value) blockers.push(t('builds.create.saveReadiness.reasons.sailors', {
      current: form.sailors,
      minimum: sailorMinimum.value,
    }))
    if (crewOverLimit.value) blockers.push(t('builds.create.saveReadiness.reasons.crew', {
      current: crewTotal.value,
      maximum: crewCapacity.value,
    }))
    for (const index of [5, 6, 7, 8]) {
      if (form[`upgrade_${index}`] && isUpgradeSlotDisabled(index)) {
        blockers.push(t(`builds.create.saveReadiness.reasons.upgrade${index}`))
      }
    }
    if (!inventory.allWeaponsValid.value) blockers.push(t('builds.create.saveReadiness.reasons.weapons'))
    if (specialCrewOverCapacity.value) blockers.push(t('builds.create.saveReadiness.reasons.specialists', {
      maximum: specialCrewLimit.value,
    }))
    return blockers
  })
  const canSubmit = computed(() => submitBlockers.value.length === 0 && !saving.value)

  return {
    equipmentUpgradeCount,
    upgradeAccess,
    selectedUpgradeNames,
    upgradeEffectTotals,
    specialCrewEffectSets,
    specialCrewEffectTotals,
    equipmentEffectTotals,
    researchUpgradeEffectTotals,
    mortarModificationEffectTotals,
    buildEffectTotals,
    buildEffectSets,
    upgradeSlot5Unlocked,
    upgradeSlot6Available,
    upgradeSlot7Available,
    upgradeSlot8Available,
    availableUpgradeSlots,
    crewCapacity,
    sailorMinimum,
    sailingEfficiency,
    crewTotal,
    crewRemaining,
    crewOverLimit,
    sailorsBelowMinimum,
    crewInvalid,
    specialCrewLimit,
    specialCrewOverCapacity,
    upgradeSlotsUsed,
    shipStatsPreview,
    buildStatRows,
    selectedUpgradeCards,
    activeEffectRows,
    submitBlockers,
    canSubmit,
    isUpgradeSlotDisabled,
    upgradeSlotPlaceholder,
    upgradeOptionsForSlot,
    upgradeGroupsForSlot,
  }
}
