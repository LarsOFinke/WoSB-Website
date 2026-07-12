<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'

import { useLocale } from '@/locales'
import { createBuild, getBuild, getBuildOptions, updateMyBuild } from '@/modules/builds/api/builds'
import { createBuildForm, equipmentUpgradeCount, slotLimits, sortShipsForDropdown, weaponArcFields } from '@/modules/builds/buildForm'
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { calculateBuildStatRows, calculateUpgradeSlotAccess, sumEffects } from '@/modules/builds/buildCalculations'
import { calculateSpecialistEffectTotals } from '@/modules/builds/specialistEffects'
import {
  crewSliderMax,
  normalizeCrewAllocation,
  setCrewAllocationValue,
  sailingEfficiencyPercent,
} from '@/modules/builds/crewAllocation'
import {
  emptyInventorySlot,
  inventoryQuantityTotal,
  isWeaponInventoryField,
  normalizeInventorySlots,
  reconcileInventorySlots,
  remainingInventoryQuantity,
  selectInventoryItem,
  setInventoryQuantity,
} from '@/modules/builds/inventorySlots'
import { absoluteFileUrl } from '@/modules/files/api/files'
import { listShips } from '@/modules/ships/api/ships'
import { useSession } from '@/modules/accounts/session'

const props = defineProps({
  id: { type: String, default: '' },
})

const router = useRouter()
const { optionLabel, t } = useLocale()
const { user } = useSession()
const isEditing = computed(() => Boolean(props.id))
const suppressShipChange = ref(false)

const ships = ref([])
const optionCatalog = ref({ categories: [], options: {}, stat_definitions: [], research_upgrade_slot_effects: {}, limits: {} })
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const buildTypeOptions = computed(() => [
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])

function optionsFor(categoryKey) {
  return (optionCatalog.value.options?.[categoryKey] || [])
    .map((option) => option.name)
    .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
}

const form = reactive(createBuildForm())

const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(form.ship_id)))
const availableWeaponArcs = computed(() => weaponArcFields.filter((arc) => weaponCapacityForField(arc.fieldName) > 0))
function optionMeta(categoryKey, name) {
  return (optionCatalog.value.options?.[categoryKey] || []).find((option) => option.name === name)
}

function optionEffects(categoryKey, name) {
  return optionMeta(categoryKey, name)?.stat_effects || {}
}

function optionImage(categoryKey, name) {
  return absoluteFileUrl(optionMeta(categoryKey, name)?.image_url) || slotPlaceholderSrc
}

function inventoryCategory(fieldName) {
  if (fieldName.includes('weapon')) return 'weapon'
  if (fieldName === 'special_crew_slots') return 'special_crew'
  if (fieldName === 'ammunition_slots') return 'ammunition'
  if (fieldName === 'consumable_slots') return 'consumable'
  if (fieldName === 'hold_slots') return 'hold'
  return ''
}

function inventoryImage(fieldName, item) {
  return optionImage(inventoryCategory(fieldName), item)
}

function upgradeEffects(name) {
  return optionEffects('upgrade', name)
}

function specialCrewEffects(name) {
  return optionEffects('special_crew', name)
}

function effectValue(value) {
  const number = Number(value)
  if (!Number.isFinite(number) || number === 0) return ''
  return number > 0 ? `+${number}` : String(number)
}

function statDefinitionForEffect(key) {
  return (optionCatalog.value.stat_definitions || []).find(
    (definition) => definition.pct_effect === key || definition.flat_effect === key || definition.key === key,
  )
}

function statLabel(key) {
  const definition = statDefinitionForEffect(key)
  const path = `builds.statLabels.${definition?.key || key}`
  const translated = t(path)
  return translated === path ? (definition?.label || String(key).replaceAll('_', ' ')) : translated
}

function formatEffects(name, categoryKey = 'upgrade') {
  const effects = optionEffects(categoryKey, name)
  const entries = Object.entries(effects).filter(([, value]) => Number(value) !== 0)
  if (!entries.length) return ''
  return entries.map(([key, value]) => {
    if (key.endsWith('_enabled')) return statLabel(key)
    return `${statLabel(key)} ${effectValue(value)}${key.endsWith('_pct') ? '%' : ''}`
  }).join(' · ')
}


const baseCrewCapacity = computed(() => selectedShip.value?.crew_capacity || 0)
const baseSailorMinimum = computed(() => selectedShip.value?.sailor_minimum || 0)
const firstFourUpgradeEffects = computed(() => sumEffects(
  ...[form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4]
    .filter(Boolean)
    .map((name) => upgradeEffects(name)),
))
const upgradeEffectTotals = computed(() => sumEffects(
  ...[form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4, form.upgrade_5, form.upgrade_6]
    .filter(Boolean)
    .map((name) => upgradeEffects(name)),
))
const specialCrewEffectTotals = computed(() => calculateSpecialistEffectTotals({
  slots: normalizeInventorySlots(form.special_crew_slots),
  effectForItem: specialCrewEffects,
  crew: {
    sailors: form.sailors,
    soldiers: form.soldiers,
    musketeers: form.musketeers,
    mercenaries: form.mercenaries,
  },
}))
const equipmentEffectTotals = computed(() => sumEffects(
  optionEffects('sail', form.sails),
  optionEffects('lantern', form.lantern),
))
const researchUpgradeEffectTotals = computed(() => (
  form.research_upgrade_slot_unlocked
    ? optionCatalog.value.research_upgrade_slot_effects || {}
    : {}
))
const buildEffectTotals = computed(() => sumEffects(
  equipmentEffectTotals.value,
  upgradeEffectTotals.value,
  specialCrewEffectTotals.value,
  researchUpgradeEffectTotals.value,
))
const upgradeAccess = computed(() => calculateUpgradeSlotAccess({
  shipUpgradeSlots: selectedShip.value?.upgrade_slots || 0,
  unlockEffectSlots: firstFourUpgradeEffects.value.extra_upgrade_slots || 0,
  researchUpgradeSlotUnlocked: form.research_upgrade_slot_unlocked,
  slotLimit: equipmentUpgradeCount,
}))
const upgradeSlot5Unlocked = computed(() => upgradeAccess.value.slot5Unlocked)
const upgradeSlot6Available = computed(() => upgradeAccess.value.slot6Available)
const availableUpgradeSlots = computed(() => upgradeAccess.value.availableSlots)
const crewCapacity = computed(() => Math.max(0, Math.round(
  baseCrewCapacity.value * (1 + (Number(buildEffectTotals.value.crew_capacity_pct) || 0) / 100)
  + (Number(buildEffectTotals.value.crew_capacity) || 0),
)))
const sailorMinimum = computed(() => Math.max(0, baseSailorMinimum.value + (Number(buildEffectTotals.value.sailor_minimum) || 0)))
const sailingEfficiency = computed(() => sailingEfficiencyPercent(form.sailors, sailorMinimum.value))

const crewTotal = computed(
  () => Number(form.sailors) + Number(form.soldiers) + Number(form.musketeers) + Number(form.mercenaries),
)
const crewRemaining = computed(() => Math.max(0, crewCapacity.value - crewTotal.value))
const crewOverLimit = computed(() => crewCapacity.value > 0 && crewTotal.value > crewCapacity.value)
const sailorsBelowMinimum = computed(() => Boolean(selectedShip.value) && Number(form.sailors) < sailorMinimum.value)
const crewInvalid = computed(() => crewOverLimit.value || sailorsBelowMinimum.value)
const specialCrewLimit = computed(() => Math.max(1, Number(optionCatalog.value.limits?.special_crew_rows || optionCatalog.value.limits?.special_crew_total) || 8))
const specialCrewOverCapacity = computed(() => slotCount('special_crew_slots') > specialCrewLimit.value)

const upgradeSlotsUsed = computed(() =>
  [form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4, form.upgrade_5, form.upgrade_6].filter(Boolean).length,
)
const shipStatsPreview = computed(() => ({
  weaponTotal: allWeaponQuantityTotal(),
  specialCrew: slotCount('special_crew_slots'),
  inventorySlots: slotCount('ammunition_slots') + slotCount('consumable_slots') + slotCount('hold_slots'),
  upgrades: upgradeSlotsUsed.value,
}))

const statDefinitions = computed(() => optionCatalog.value.stat_definitions || [])
const buildStatRows = computed(() => calculateBuildStatRows({
  ship: selectedShip.value,
  definitions: statDefinitions.value,
  effects: buildEffectTotals.value,
}).map((row) => {
  const path = `builds.statLabels.${row.key}`
  const translated = t(path)
  return {
    ...row,
    label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated,
  }
}))

const selectedUpgradeCards = computed(() => Array.from({ length: equipmentUpgradeCount }, (_, offset) => {
  const index = offset + 1
  const name = form[`upgrade_${index}`]
  return {
    index,
    name,
    label: name ? optionLabel(name) : '',
    effects: name ? formatEffects(name) : '',
    locked: isUpgradeSlotDisabled(index),
  }
}))

const activeEffectRows = computed(() => buildStatRows.value.filter((row) => Number(row.modifier || 0) !== 0))

const submitBlockers = computed(() => {
  const blockers = []
  if (!form.build_name.trim()) blockers.push(t('builds.create.saveReadiness.reasons.name'))
  if (!form.ship_id) blockers.push(t('builds.create.saveReadiness.reasons.ship'))
  if (sailorsBelowMinimum.value) blockers.push(t('builds.create.saveReadiness.reasons.sailors', { current: form.sailors, minimum: sailorMinimum.value }))
  if (crewOverLimit.value) blockers.push(t('builds.create.saveReadiness.reasons.crew', { current: crewTotal.value, maximum: crewCapacity.value }))
  if (form.upgrade_5 && !upgradeSlot5Unlocked.value) blockers.push(t('builds.create.saveReadiness.reasons.upgrade5'))
  if (form.upgrade_6 && !upgradeSlot6Available.value) blockers.push(t('builds.create.saveReadiness.reasons.upgrade6'))
  if (!allWeaponsValid.value) blockers.push(t('builds.create.saveReadiness.reasons.weapons'))
  if (specialCrewOverCapacity.value) blockers.push(t('builds.create.saveReadiness.reasons.specialists', { maximum: specialCrewLimit.value }))
  return blockers
})

const canSubmit = computed(() => submitBlockers.value.length === 0 && !saving.value)

function slotCount(fieldName) {
  return normalizeInventorySlots(form[fieldName]).length
}

function slotQuantityTotal(fieldName) {
  return inventoryQuantityTotal(form[fieldName])
}

function allWeaponQuantityTotal() {
  return weaponArcFields.reduce((total, arc) => total + slotQuantityTotal(arc.fieldName), 0)
}

function isOptionUsed(slots, option, currentIndex) {
  return slots.some((slot, index) => index !== currentIndex && slot.item === option)
}

function upgradeOptionsForSlot(index) {
  const current = form[`upgrade_${index}`]
  const selectedElsewhere = new Set(
    Array.from({ length: equipmentUpgradeCount }, (_, offset) => offset + 1)
      .filter((slotIndex) => slotIndex !== index)
      .map((slotIndex) => form[`upgrade_${slotIndex}`])
      .filter(Boolean),
  )
  return optionsFor('upgrade').filter((option) => option === current || !selectedElsewhere.has(option))
}


function weaponSlotTypeForField(fieldName) {
  return {
    front_weapon_slots: 'weapon_front',
    rear_weapon_slots: 'weapon_rear',
    port_weapon_slots: 'weapon_port',
    starboard_weapon_slots: 'weapon_starboard',
    mortar_weapon_slots: 'weapon_mortar',
    special_weapon_slots: 'weapon_special',
  }[fieldName]
}

function weaponCapacityForField(fieldName) {
  if (!selectedShip.value) return slotLimits[fieldName] || 0
  const capacityMap = {
    front_weapon_slots: selectedShip.value.front_weapon_capacity,
    rear_weapon_slots: selectedShip.value.rear_weapon_capacity,
    port_weapon_slots: selectedShip.value.broadside_weapon_capacity,
    starboard_weapon_slots: selectedShip.value.broadside_weapon_capacity,
    mortar_weapon_slots: selectedShip.value.mortar_weapon_capacity,
    special_weapon_slots: selectedShip.value.special_weapon_capacity,
  }
  return Math.max(0, Number(capacityMap[fieldName]) || 0)
}

function slotLimitForField(fieldName) {
  if (weaponSlotTypeForField(fieldName)) {
    return Math.min(slotLimits[fieldName] || 0, Math.max(weaponCapacityForField(fieldName), 0))
  }
  return slotLimits[fieldName]
}

function isWeaponOptionAllowedForField(option, fieldName) {
  const slotType = weaponSlotTypeForField(fieldName)
  if (!slotType) return true
  const allowedSlots = Array.isArray(option.allowed_slot_types) ? option.allowed_slot_types : []
  if (!allowedSlots.includes(slotType)) return false
  if (slotType === 'weapon_mortar') {
    const maxCaliber = Number(selectedShip.value?.max_mortar_caliber_inches)
    const optionCaliber = Number(option.weapon_caliber_inches)
    if (Number.isFinite(maxCaliber) && Number.isFinite(optionCaliber) && optionCaliber > maxCaliber) return false
    return ['mortar', 'mortar_launcher'].includes(option.option_kind)
  }
  if (slotType === 'weapon_special') return option.option_kind === 'special_weapon'
  return !['mortar', 'mortar_launcher', 'special_weapon'].includes(option.option_kind)
}

function weaponOptionsForField(fieldName, currentIndex) {
  if (!selectedShip.value || weaponCapacityForField(fieldName) <= 0) return []
  const current = form[fieldName]?.[currentIndex]?.item || ''
  const selectedElsewhere = new Set(
    (form[fieldName] || [])
      .filter((_, index) => index !== currentIndex)
      .map((slot) => slot.item)
      .filter(Boolean),
  )
  return (optionCatalog.value.options?.weapon || [])
    .filter((option) => isWeaponOptionAllowedForField(option, fieldName))
    .map((option) => option.name)
    .filter((option) => option === current || !selectedElsewhere.has(option))
    .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
}

function isWeaponFieldUnavailable(fieldName) {
  return Boolean(weaponSlotTypeForField(fieldName)) && weaponCapacityForField(fieldName) <= 0
}

function weaponFieldOverCapacity(fieldName) {
  return slotQuantityTotal(fieldName) > weaponCapacityForField(fieldName)
}

function weaponSelectionInvalid(fieldName, optionName) {
  if (!optionName || !isWeaponInventoryField(fieldName)) return false
  const option = optionMeta('weapon', optionName)
  return !option || !isWeaponOptionAllowedForField(option, fieldName)
}

const allWeaponsValid = computed(() => weaponArcFields.every((arc) => {
  if (weaponFieldOverCapacity(arc.fieldName)) return false
  return normalizeInventorySlots(form[arc.fieldName]).every((slot) => !weaponSelectionInvalid(arc.fieldName, slot.item))
}))

function isUpgradeSlotDisabled(index) {
  if (index === 5) return !upgradeSlot5Unlocked.value
  if (index === 6) return !upgradeSlot6Available.value
  return false
}

function upgradeSlotPlaceholder(index) {
  if (index === 5 && !upgradeSlot5Unlocked.value) return t('builds.create.equipment.lockedUpgrade5')
  if (index === 6 && !upgradeSlot6Available.value) return t('builds.create.equipment.lockedUpgrade6')
  return t('common.empty')
}

function quantityCapacityForField(fieldName) {
  if (isWeaponInventoryField(fieldName)) return weaponCapacityForField(fieldName)
  return null
}

function quantityMaxForField(fieldName, index) {
  const capacity = quantityCapacityForField(fieldName)
  if (capacity === null) return 999999
  return Math.max(1, remainingInventoryQuantity(form[fieldName], index, capacity))
}

function inventoryReconcileOptions(fieldName) {
  return {
    isItemAllowed: (item) => !weaponSelectionInvalid(fieldName, item),
    maxTotalQuantity: quantityCapacityForField(fieldName),
  }
}

function replaceInventorySlots(fieldName, slots) {
  form[fieldName].splice(0, form[fieldName].length, ...slots)
}

function reconcileInventoryField(fieldName) {
  replaceInventorySlots(
    fieldName,
    reconcileInventorySlots(form[fieldName], slotLimitForField(fieldName), inventoryReconcileOptions(fieldName)),
  )
}

function onInventoryItemChange(fieldName, index, event) {
  replaceInventorySlots(
    fieldName,
    selectInventoryItem(
      form[fieldName],
      index,
      event.target.value,
      slotLimitForField(fieldName),
      inventoryReconcileOptions(fieldName),
    ),
  )
}

function onInventoryQuantityChange(fieldName, index, event) {
  replaceInventorySlots(
    fieldName,
    setInventoryQuantity(
      form[fieldName],
      index,
      event.target.value,
      slotLimitForField(fieldName),
      inventoryReconcileOptions(fieldName),
    ),
  )
}

function currentCrewAllocation() {
  return {
    sailors: form.sailors,
    musketeers: form.musketeers,
    soldiers: form.soldiers,
    mercenaries: form.mercenaries,
  }
}

function applyCrewAllocation(allocation) {
  form.sailors = allocation.sailors
  form.musketeers = allocation.musketeers
  form.soldiers = allocation.soldiers
  form.mercenaries = allocation.mercenaries
}

function crewMaxFor(fieldName) {
  return crewSliderMax(currentCrewAllocation(), fieldName, crewCapacity.value, sailorMinimum.value)
}

function onCrewSliderInput(fieldName, event) {
  applyCrewAllocation(
    setCrewAllocationValue(
      currentCrewAllocation(),
      fieldName,
      event.target.value,
      crewCapacity.value,
      sailorMinimum.value,
    ),
  )
}

function normalizeCurrentCrew() {
  applyCrewAllocation(normalizeCrewAllocation(currentCrewAllocation(), crewCapacity.value, sailorMinimum.value))
}

function resetCrewAllocation() {
  applyCrewAllocation(normalizeCrewAllocation({ sailors: 0 }, crewCapacity.value, sailorMinimum.value))
}

function resetSlots() {
  for (const fieldName of Object.keys(slotLimits)) {
    form[fieldName] = slotLimitForField(fieldName) > 0 ? [emptyInventorySlot()] : []
  }
}

function hydrateBuild(build) {
  for (const fieldName of [
    'build_name', 'build_type', 'ship_id', 'sails', 'upgrade_1', 'upgrade_2', 'upgrade_3',
    'upgrade_4', 'upgrade_5', 'upgrade_6', 'lantern', 'research_upgrade_slot_unlocked',
    'sailors', 'soldiers', 'musketeers', 'mercenaries', 'details',
  ]) {
    form[fieldName] = build[fieldName] ?? form[fieldName]
  }
  for (const fieldName of Object.keys(slotLimits)) {
    const slots = Array.isArray(build[fieldName]) ? build[fieldName].map((slot) => ({ ...slot })) : []
    form[fieldName] = slots.length ? slots : (slotLimitForField(fieldName) > 0 ? [emptyInventorySlot()] : [])
  }
}

function buildPayload() {
  return {
    ...form,
    ship_id: Number(form.ship_id),
    sailors: Number(form.sailors),
    soldiers: Number(form.soldiers),
    musketeers: Number(form.musketeers),
    mercenaries: Number(form.mercenaries),
    front_weapon_slots: normalizeInventorySlots(form.front_weapon_slots),
    rear_weapon_slots: normalizeInventorySlots(form.rear_weapon_slots),
    port_weapon_slots: normalizeInventorySlots(form.port_weapon_slots),
    starboard_weapon_slots: normalizeInventorySlots(form.starboard_weapon_slots),
    mortar_weapon_slots: normalizeInventorySlots(form.mortar_weapon_slots),
    special_weapon_slots: normalizeInventorySlots(form.special_weapon_slots),
    special_crew_slots: normalizeInventorySlots(form.special_crew_slots).map((slot) => ({ ...slot, quantity: 1 })),
    ammunition_slots: normalizeInventorySlots(form.ammunition_slots),
    consumable_slots: normalizeInventorySlots(form.consumable_slots),
    hold_slots: normalizeInventorySlots(form.hold_slots),
  }
}

async function saveBuild() {
  error.value = ''
  if (!canSubmit.value) return

  saving.value = true
  try {
    const saved = isEditing.value
      ? await updateMyBuild(props.id, buildPayload())
      : await createBuild(buildPayload())
    await router.push(`/builds/${saved.id}`)
  } catch (err) {
    error.value = err.message || t(isEditing.value ? 'builds.edit.saveError' : 'builds.create.saveError')
  } finally {
    saving.value = false
  }
}

let optionRequestId = 0
watch(
  () => form.ship_id,
  async (shipId) => {
    if (suppressShipChange.value) return
    resetCrewAllocation()
    if (!shipId) return
    const requestId = ++optionRequestId
    try {
      const options = await getBuildOptions(Number(shipId))
      if (requestId !== optionRequestId) return
      optionCatalog.value = options
      for (const arc of weaponArcFields) reconcileInventoryField(arc.fieldName)
    } catch (err) {
      if (requestId === optionRequestId) error.value = err.message || t('builds.create.loadError')
    }
  },
)

watch([crewCapacity, sailorMinimum], () => {
  normalizeCurrentCrew()
})

watch(upgradeSlot5Unlocked, (isUnlocked) => {
  if (!isUnlocked) {
    form.upgrade_5 = ''
  }
})

watch(upgradeSlot6Available, (isAvailable) => {
  if (!isAvailable) {
    form.upgrade_6 = ''
  }
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const shipRows = await listShips()
    ships.value = sortShipsForDropdown(shipRows)

    if (isEditing.value) {
      const existing = await getBuild(props.id)
      if (Number(existing.owner_id) !== Number(user.value?.id) || existing.is_official_template) {
        throw new Error(t('builds.edit.notAllowed'))
      }
      suppressShipChange.value = true
      form.ship_id = existing.ship_id
      optionCatalog.value = await getBuildOptions(existing.ship_id)
      hydrateBuild(existing)
      for (const fieldName of Object.keys(slotLimits)) reconcileInventoryField(fieldName)
      suppressShipChange.value = false
    } else {
      form.ship_id = ships.value[0]?.id || ''
      optionCatalog.value = await getBuildOptions(form.ship_id || null)
      resetSlots()
      resetCrewAllocation()
    }
  } catch (err) {
    suppressShipChange.value = false
    error.value = err.message || t(isEditing.value ? 'builds.edit.loadError' : 'builds.create.loadError')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="build-create-page" aria-labelledby="build-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean" @submit.prevent="saveBuild">
      <div class="create-topline">
        <div>
          <h1 id="build-create-title">{{ t(isEditing ? 'builds.edit.title' : 'builds.create.title') }}</h1>
          <p>{{ t(isEditing ? 'builds.edit.subtitle' : 'builds.create.subtitle') }}</p>
        </div>
        <RouterLink class="small-action" :to="isEditing ? `/builds/${props.id}` : '/builds'">{{ t('common.back') }}</RouterLink>
      </div>

      <section class="wire-section form-section identity-section" :aria-label="t('builds.create.sections.identity')">
        <div class="section-title">
          <span>01</span>
          <h2>{{ t('builds.create.sections.identity') }}</h2>
        </div>
        <div class="section-fields two-fields">
          <label class="input-panel embedded-field">
            <input
              v-model="form.build_name"
              required
              maxlength="140"
              :placeholder="t('builds.create.buildNamePlaceholder')"
              :aria-label="t('builds.create.buildName')"
            />
          </label>
          <label class="input-panel embedded-field">
            <select v-model="form.build_type" required :aria-label="t('builds.create.buildType')">
              <option v-for="option in buildTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
      </section>

      <section class="wire-section form-section ship-section" :aria-label="t('builds.create.sections.ship')">
        <div class="section-title">
          <span>02</span>
          <h2>{{ t('builds.create.sections.ship') }}</h2>
        </div>
        <label class="input-panel embedded-field ship-select-field">
          <select v-model="form.ship_id" required :disabled="loading" :aria-label="t('builds.create.ship')">
            <option value="" disabled>{{ t('builds.create.selectShip') }}</option>
            <option v-for="ship in ships" :key="ship.id" :value="ship.id">
              {{ ship.name }}
            </option>
          </select>
        </label>
        <BuildStatCommandDeck
          v-if="selectedShip"
          :ship="selectedShip"
          :stat-rows="buildStatRows"
          :upgrade-slots="selectedUpgradeCards"
          :effect-rows="activeEffectRows"
          :crew-total="crewTotal"
          :crew-capacity="crewCapacity"
          :crew-remaining="crewRemaining"
          :weapon-total="shipStatsPreview.weaponTotal"
          :upgrade-slots-available="availableUpgradeSlots"
          :special-crew-total="shipStatsPreview.specialCrew"
        />
      </section>

      <section class="wire-section form-section equipment-section" :aria-label="t('builds.create.sections.equipment')">
        <div class="section-title">
          <span>03</span>
          <h2>{{ t('builds.create.sections.equipment') }}</h2>
        </div>
        <div class="equipment-unified-grid">
          <label class="square-slot equipment-slot equipment-slot-sail">
            <span class="slot-visual"><img :src="optionImage('sail', form.sails)" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.sail') }}</span>
            <span class="select-shell">
              <select v-model="form.sails" :aria-label="t('builds.create.equipment.sail')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('sail')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>

          <label v-for="index in equipmentUpgradeCount" :key="index" class="square-slot equipment-slot equipment-slot-upgrade">
            <span class="slot-visual"><img :src="optionImage('upgrade', form[`upgrade_${index}`])" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.upgrade', { index }) }}</span>
            <span class="select-shell">
              <select
                v-model="form[`upgrade_${index}`]"
                :aria-label="t('builds.create.equipment.upgrade', { index })"
                :disabled="isUpgradeSlotDisabled(index)"
              >
                <option value="">{{ upgradeSlotPlaceholder(index) }}</option>
                <option v-for="option in upgradeOptionsForSlot(index)" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
              <small v-if="form[`upgrade_${index}`]" class="slot-effect-text">{{ formatEffects(form[`upgrade_${index}`]) }}</small>
            </span>
          </label>

          <label class="square-slot equipment-slot equipment-slot-lantern">
            <span class="slot-visual"><img :src="optionImage('lantern', form.lantern)" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.lantern') }}</span>
            <span class="select-shell">
              <select v-model="form.lantern" :aria-label="t('builds.create.equipment.lantern')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('lantern')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>
        </div>
        <button
          type="button"
          class="research-slot-toggle"
          :class="{ 'is-active': form.research_upgrade_slot_unlocked }"
          :aria-pressed="form.research_upgrade_slot_unlocked"
          @click="form.research_upgrade_slot_unlocked = !form.research_upgrade_slot_unlocked"
        >
          <span>{{ form.research_upgrade_slot_unlocked ? '✓' : '+' }}</span>
          <strong>{{ t('builds.create.equipment.researchUpgradeSlot') }}</strong>
          <small>{{ t('builds.create.equipment.researchUpgradeSlotHint') }}</small>
        </button>
      </section>

      <section class="wire-section form-section weapons-section" :aria-label="t('builds.create.sections.weapons')">
        <div class="section-title">
          <span>04</span>
          <h2>{{ t('builds.create.sections.weapons') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('builds.create.weapons.hint') }}</p>
        <div class="inventory-grid weapon-arc-grid weapon-arc-grid--adaptive">
          <div v-for="arc in availableWeaponArcs" :key="arc.fieldName" class="inventory-panel weapon-arc-panel">
            <div class="inventory-heading">
              <strong>{{ t(arc.labelKey) }}</strong>
              <span>{{ t('builds.create.weapons.capacity', { count: slotQuantityTotal(arc.fieldName), max: weaponCapacityForField(arc.fieldName) }) }}</span>
            </div>
            <p v-if="isWeaponFieldUnavailable(arc.fieldName)" class="slot-hint">{{ t('builds.create.weapons.unavailable') }}</p>
            <label v-for="(slot, index) in form[arc.fieldName]" :key="`${arc.fieldName}-${index}`" class="inventory-slot-select with-quantity" :class="{ 'is-invalid': weaponSelectionInvalid(arc.fieldName, slot.item) || weaponFieldOverCapacity(arc.fieldName) }">
              <span class="slot-image-cell">
                <img :src="inventoryImage(arc.fieldName, slot.item)" :alt="t(arc.altKey, { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange(arc.fieldName, index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in weaponOptionsForField(arc.fieldName, index)"
                  :key="option"
                  :value="option"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                :max="quantityMaxForField(arc.fieldName, index)"
                :aria-label="t('common.quantity')"
                @input="onInventoryQuantityChange(arc.fieldName, index, $event)"
              />
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section special-crew-section" :aria-label="t('builds.create.sections.specialCrew')">
        <div class="section-title">
          <span>05</span>
          <h2>{{ t('builds.create.sections.specialCrew') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('builds.create.specialCrew.hint') }}</p>
        <div class="inventory-grid special-crew-grid single-column">
          <div class="inventory-panel special-crew-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.specialCrew.title') }}</strong>
              <span>{{ t('builds.create.inventory.limitedSlotCount', { count: slotCount('special_crew_slots'), max: specialCrewLimit }) }}</span>
            </div>
            <label v-for="(slot, index) in form.special_crew_slots" :key="`special-crew-${index}`" class="inventory-slot-select specialist-slot-select">
              <span class="slot-image-cell">
                <img :src="inventoryImage('special_crew_slots', slot.item)" :alt="t('builds.create.specialCrew.alt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('special_crew_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('special_crew')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.special_crew_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <small v-if="slot.item" class="slot-effect-text">{{ formatEffects(slot.item, 'special_crew') }}</small>
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section crew-section" :aria-label="t('builds.create.sections.crew')">
        <div class="section-title">
          <span>06</span>
          <h2>{{ t('builds.create.sections.crew') }}</h2>
        </div>
        <div class="crew-allocation-console" :class="{ 'is-invalid': crewInvalid }">
          <div class="crew-allocation-header">
            <div>
              <span>{{ t('builds.crewConsole.eyebrow') }}</span>
              <strong>{{ t('builds.crewConsole.title') }}</strong>
            </div>
            <div class="crew-allocation-total">
              <strong>{{ crewTotal }}/{{ crewCapacity || '—' }}</strong>
              <span>{{ t('builds.create.crew.free', { value: crewRemaining }) }}</span>
            </div>
          </div>
          <div class="crew-allocation-meter" :aria-label="t('builds.create.crew.total', { current: crewTotal, max: crewCapacity || '—' })">
            <span class="crew-meter-sailors" :style="{ width: `${crewCapacity ? (Number(form.sailors) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-musketeers" :style="{ width: `${crewCapacity ? (Number(form.musketeers) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-soldiers" :style="{ width: `${crewCapacity ? (Number(form.soldiers) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-mercenaries" :style="{ width: `${crewCapacity ? (Number(form.mercenaries) / crewCapacity) * 100 : 0}%` }"></span>
          </div>
          <div class="crew-allocation-legend">
            <span>{{ t('builds.create.crew.sailorMinimum', { value: sailorMinimum }) }}</span>
            <span>{{ t('builds.crewConsole.dynamicLimit') }}</span>
            <span>{{ t('builds.create.crew.workingSpeed', { value: sailingEfficiency }) }}</span>
            <span v-if="sailorsBelowMinimum" class="crew-warning">{{ t('builds.create.crew.tooFewSailors', { current: form.sailors, minimum: sailorMinimum }) }}</span>
            <span v-if="crewOverLimit" class="crew-warning">{{ t('builds.create.crew.tooManyCrew') }}</span>
          </div>

          <div class="crew-grid section-fields">
            <label class="crew-slider-card crew-sailors">
              <span><small>{{ t('builds.create.crew.sailors') }}</small><strong>{{ form.sailors }}</strong></span>
              <input :value="form.sailors" type="range" min="0" :max="crewMaxFor('sailors')" @input="onCrewSliderInput('sailors', $event)" />
              <small>0–{{ crewMaxFor('sailors') }}</small>
            </label>

            <label class="crew-slider-card crew-musketeers">
              <span><small>{{ t('builds.create.crew.musketeers') }}</small><strong>{{ form.musketeers }}</strong></span>
              <input :value="form.musketeers" type="range" min="0" :max="crewMaxFor('musketeers')" @input="onCrewSliderInput('musketeers', $event)" />
              <small>0–{{ crewMaxFor('musketeers') }}</small>
            </label>

            <label class="crew-slider-card crew-soldiers">
              <span><small>{{ t('builds.create.crew.soldiers') }}</small><strong>{{ form.soldiers }}</strong></span>
              <input :value="form.soldiers" type="range" min="0" :max="crewMaxFor('soldiers')" @input="onCrewSliderInput('soldiers', $event)" />
              <small>0–{{ crewMaxFor('soldiers') }}</small>
            </label>

            <label class="crew-slider-card crew-mercenaries">
              <span><small>{{ t('builds.create.crew.mercenaries') }}</small><strong>{{ form.mercenaries }}</strong></span>
              <input :value="form.mercenaries" type="range" min="0" :max="crewMaxFor('mercenaries')" @input="onCrewSliderInput('mercenaries', $event)" />
              <small>0–{{ crewMaxFor('mercenaries') }}</small>
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section inventory-section" :aria-label="t('builds.create.sections.inventory')">
        <div class="section-title">
          <span>07</span>
          <h2>{{ t('builds.create.sections.inventory') }}</h2>
        </div>
        <div class="inventory-grid three-columns">
          <div class="inventory-panel ammunition-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.ammunition') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: slotCount('ammunition_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.ammunitionHint') }}</p>
            <label v-for="(slot, index) in form.ammunition_slots" :key="`ammo-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('ammunition_slots', slot.item)" :alt="t('builds.create.inventory.ammunitionAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('ammunition_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('ammunition')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.ammunition_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('ammunition_slots', index, $event)"
              />
            </label>
          </div>

          <div class="inventory-panel consumable-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.consumables') }}</strong>
              <span>{{ t('builds.create.inventory.limitedSlotCount', { count: slotCount('consumable_slots'), max: 3 }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.consumablesHint') }}</p>
            <label v-for="(slot, index) in form.consumable_slots" :key="`consumable-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('consumable_slots', slot.item)" :alt="t('builds.create.inventory.consumableAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('consumable_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('consumable')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.consumable_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('consumable_slots', index, $event)"
              />
            </label>
          </div>

          <div class="inventory-panel hold-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.hold') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: slotCount('hold_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.holdHint') }}</p>
            <label v-for="(slot, index) in form.hold_slots" :key="`hold-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('hold_slots', slot.item)" :alt="t('builds.create.inventory.holdAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('hold_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('hold')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.hold_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('hold_slots', index, $event)"
              />
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section details-section" :aria-label="t('builds.create.sections.details')">
        <div class="section-title">
          <span>08</span>
          <h2>{{ t('builds.create.sections.details') }}</h2>
        </div>
        <label class="input-panel embedded-field details-field">
          <textarea v-model="form.details" rows="4" maxlength="3000" :placeholder="t('builds.create.detailsPlaceholder')"></textarea>
        </label>
      </section>

      <section class="wire-section save-readiness" :class="{ 'is-ready': submitBlockers.length === 0 }" aria-live="polite">
        <div>
          <strong>{{ t(submitBlockers.length ? 'builds.create.saveReadiness.blockedTitle' : 'builds.create.saveReadiness.readyTitle') }}</strong>
          <p>{{ t(submitBlockers.length ? 'builds.create.saveReadiness.blockedHint' : 'builds.create.saveReadiness.readyHint') }}</p>
        </div>
        <ul v-if="submitBlockers.length">
          <li v-for="blocker in submitBlockers" :key="blocker">{{ blocker }}</li>
        </ul>
      </section>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="form-actions">
        <RouterLink class="wire-section form-button" :to="isEditing ? `/builds/${props.id}` : '/builds'">{{ t('common.cancel') }}</RouterLink>
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving ? t(isEditing ? 'builds.edit.saving' : 'builds.create.saving') : t(isEditing ? 'builds.edit.save' : 'builds.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
