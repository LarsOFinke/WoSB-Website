<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { createBuild, getBuildOptions } from '@/modules/builds/api/builds'
import {
  emptyInventorySlot,
  isWeaponInventoryField,
  normalizeInventorySlots,
  reconcileInventorySlots,
  selectInventoryItem,
  setInventoryQuantity,
} from '@/modules/builds/inventorySlots'
import { listShips } from '@/modules/ships/api/ships'

const router = useRouter()
const { optionLabel, t } = useLocale()

const ships = ref([])
const optionCatalog = ref({ categories: [], options: {} })
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const slotPlaceholderSrc = '/icons/slot-placeholder.svg'
const equipmentUpgradeCount = 6
const weaponArcFields = [
  { fieldName: 'front_weapon_slots', labelKey: 'builds.create.weapons.front', altKey: 'builds.create.weapons.frontAlt' },
  { fieldName: 'rear_weapon_slots', labelKey: 'builds.create.weapons.rear', altKey: 'builds.create.weapons.rearAlt' },
  { fieldName: 'port_weapon_slots', labelKey: 'builds.create.weapons.port', altKey: 'builds.create.weapons.portAlt' },
  { fieldName: 'starboard_weapon_slots', labelKey: 'builds.create.weapons.starboard', altKey: 'builds.create.weapons.starboardAlt' },
  { fieldName: 'mortar_weapon_slots', labelKey: 'builds.create.weapons.mortar', altKey: 'builds.create.weapons.mortarAlt' },
]

const buildTypeOptions = computed(() => [
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])

const slotLimits = {
  front_weapon_slots: 12,
  rear_weapon_slots: 12,
  port_weapon_slots: 12,
  starboard_weapon_slots: 12,
  mortar_weapon_slots: 8,
  special_crew_slots: 8,
  ammunition_slots: 12,
  consumable_slots: 3,
  hold_slots: 24,
}

function optionsFor(categoryKey) {
  return (optionCatalog.value.options?.[categoryKey] || [])
    .map((option) => option.name)
    .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
}

function sortShipsForDropdown(shipRows) {
  return [...shipRows].sort((left, right) => {
    const rateDiff = Number(right.rate || 0) - Number(left.rate || 0)
    if (rateDiff !== 0) return rateDiff
    return String(left.name || '').localeCompare(String(right.name || ''), undefined, { sensitivity: 'base' })
  })
}

const form = reactive({
  build_name: '',
  build_type: 'balanced',
  ship_id: '',
  sails: '',
  upgrade_1: '',
  upgrade_2: '',
  upgrade_3: '',
  upgrade_4: '',
  upgrade_5: '',
  upgrade_6: '',
  lantern: '',
  sailors: 0,
  soldiers: 0,
  musketeers: 0,
  mercenaries: 0,
  front_weapon_slots: [emptyInventorySlot()],
  rear_weapon_slots: [emptyInventorySlot()],
  port_weapon_slots: [emptyInventorySlot()],
  starboard_weapon_slots: [emptyInventorySlot()],
  mortar_weapon_slots: [emptyInventorySlot()],
  special_crew_slots: [emptyInventorySlot()],
  ammunition_slots: [emptyInventorySlot()],
  consumable_slots: [emptyInventorySlot()],
  hold_slots: [emptyInventorySlot()],
  details: '',
})

const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(form.ship_id)))
const availableWeaponArcs = computed(() => weaponArcFields.filter((arc) => weaponCapacityForField(arc.fieldName) > 0))
function optionMeta(categoryKey, name) {
  return (optionCatalog.value.options?.[categoryKey] || []).find((option) => option.name === name)
}

function optionEffects(categoryKey, name) {
  return optionMeta(categoryKey, name)?.stat_effects || {}
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
  return t(`builds.statLabels.${definition?.key || key}`)
}

function formatEffects(name, categoryKey = 'upgrade') {
  const effects = optionEffects(categoryKey, name)
  const entries = Object.entries(effects).filter(([, value]) => Number(value) !== 0)
  if (!entries.length) return ''
  return entries.map(([key, value]) => `${statLabel(key)} ${effectValue(value)}${key.endsWith('_pct') ? '%' : ''}`).join(' · ')
}

function getBaseStat(definition) {
  if (!definition?.base_field || !selectedShip.value) return null
  const value = selectedShip.value[definition.base_field]
  return Number.isFinite(Number(value)) ? Number(value) : null
}

function roundByPrecision(value, precision = 0) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const factor = 10 ** Number(precision || 0)
  const rounded = Math.round(Number(value) * factor) / factor
  return Number(precision || 0) === 0 ? Math.round(rounded) : rounded
}

function formatStatValue(value, unit, precision = 0) {
  const number = roundByPrecision(value, precision)
  if (number === null) return '—'
  return `${number}${unit ? ` ${unit}` : ''}`
}

function formatModifier(row) {
  const value = Number(row.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const sign = value > 0 ? '+' : ''
  const suffix = row.modifier_kind === 'percent' || row.unit === '%' || String(row.effect_key || '').endsWith('_pct') ? '%' : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

const baseCrewCapacity = computed(() => selectedShip.value?.crew_capacity || 0)
const baseSailorMinimum = computed(() => selectedShip.value?.sailor_minimum || 0)
const firstFourUpgradeEffects = computed(() => {
  const totals = {}
  for (const name of [form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4].filter(Boolean)) {
    for (const [key, value] of Object.entries(upgradeEffects(name))) {
      totals[key] = (Number(totals[key]) || 0) + (Number(value) || 0)
    }
  }
  return totals
})
const upgradeEffectTotals = computed(() => {
  const totals = {}
  for (const name of [form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4, form.upgrade_5, form.upgrade_6].filter(Boolean)) {
    for (const [key, value] of Object.entries(upgradeEffects(name))) {
      totals[key] = (Number(totals[key]) || 0) + (Number(value) || 0)
    }
  }
  return totals
})
const specialCrewEffectTotals = computed(() => {
  const totals = {}
  for (const slot of normalizeInventorySlots(form.special_crew_slots)) {
    for (const [key, value] of Object.entries(specialCrewEffects(slot.item))) {
      totals[key] = (Number(totals[key]) || 0) + (Number(value) || 0)
    }
  }
  return totals
})
const buildEffectTotals = computed(() => {
  const totals = { ...upgradeEffectTotals.value }
  for (const [key, value] of Object.entries(specialCrewEffectTotals.value)) {
    totals[key] = (Number(totals[key]) || 0) + (Number(value) || 0)
  }
  return totals
})
const baseUpgradeSlots = computed(() => Math.min(Math.max(Number(selectedShip.value?.upgrade_slots || 5), 0), 4))
const unlockedByUpgrades = computed(() => Math.min(Math.max(0, Number(firstFourUpgradeEffects.value.extra_upgrade_slots) || 0), equipmentUpgradeCount - baseUpgradeSlots.value))
const shipExtraUpgradeSlots = computed(() => Number(selectedShip.value?.upgrade_slots || 5) >= 6 ? 1 : 0)
const upgradeSlot5Unlocked = computed(() => unlockedByUpgrades.value >= 1)
const upgradeSlot6Available = computed(() => shipExtraUpgradeSlots.value > 0 || unlockedByUpgrades.value >= 2)
const availableUpgradeSlots = computed(() => Math.min(equipmentUpgradeCount, baseUpgradeSlots.value + Math.max(unlockedByUpgrades.value, shipExtraUpgradeSlots.value)))
const crewCapacity = computed(() => Math.max(0, baseCrewCapacity.value + (Number(buildEffectTotals.value.crew_capacity) || 0)))
const sailorMinimum = computed(() => Math.max(0, baseSailorMinimum.value + (Number(buildEffectTotals.value.sailor_minimum) || 0)))

const crewTotal = computed(
  () => Number(form.sailors) + Number(form.soldiers) + Number(form.musketeers) + Number(form.mercenaries),
)
const crewRemaining = computed(() => Math.max(0, crewCapacity.value - crewTotal.value))
const crewOverLimit = computed(() => crewCapacity.value > 0 && crewTotal.value > crewCapacity.value)
const sailorsBelowMinimum = computed(() => Number(form.sailors) < sailorMinimum.value)
const crewInvalid = computed(() => crewOverLimit.value || sailorsBelowMinimum.value)

const upgradeSlotsUsed = computed(() =>
  [form.upgrade_1, form.upgrade_2, form.upgrade_3, form.upgrade_4, form.upgrade_5, form.upgrade_6].filter(Boolean).length,
)
const shipStatsPreview = computed(() => ({
  weaponTotal: allWeaponQuantityTotal(),
  specialCrew: slotQuantityTotal('special_crew_slots'),
  inventorySlots: slotCount('ammunition_slots') + slotCount('consumable_slots') + slotCount('hold_slots'),
  upgrades: upgradeSlotsUsed.value,
}))

const statDefinitions = computed(() => optionCatalog.value.stat_definitions || [])
const buildStatRows = computed(() => statDefinitions.value
  .map((definition) => {
    const base = getBaseStat(definition)
    const pctModifier = Number(buildEffectTotals.value[definition.pct_effect] || 0)
    const flatModifier = Number(buildEffectTotals.value[definition.flat_effect] || 0)
    const modifier = pctModifier + flatModifier
    if (base === null && modifier === 0) return null

    let effective = base
    if (effective !== null && definition.pct_effect) effective *= (1 + pctModifier / 100)
    if (effective !== null && definition.flat_effect) effective += flatModifier
    if (effective === null && definition.flat_effect) effective = flatModifier

    return {
      ...definition,
      label: t(`builds.statLabels.${definition.key}`),
      base: roundByPrecision(base, definition.precision),
      modifier: roundByPrecision(modifier, definition.precision),
      effective: roundByPrecision(effective, definition.precision),
      modifier_kind: definition.pct_effect && definition.base_field ? 'percent' : 'flat',
      effect_key: definition.pct_effect || definition.flat_effect,
      isDebuff: modifier !== 0 && (definition.positive_is_good === false ? modifier > 0 : modifier < 0),
    }
  })
  .filter(Boolean))

const canSubmit = computed(
  () => form.build_name.trim()
    && form.ship_id
    && !crewInvalid.value
    && (!form.upgrade_5 || upgradeSlot5Unlocked.value)
    && (!form.upgrade_6 || upgradeSlot6Available.value)
    && allWeaponsValid.value
    && !saving.value,
)

function slotCount(fieldName) {
  return normalizeInventorySlots(form[fieldName]).length
}

function slotQuantityTotal(fieldName) {
  return normalizeInventorySlots(form[fieldName]).reduce((total, slot) => total + (Number(slot.quantity) || 1), 0)
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
  }
  return true
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

function inventoryReconcileOptions(fieldName) {
  return {
    isItemAllowed: (item) => !weaponSelectionInvalid(fieldName, item),
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

function setCrewToShipMinimum() {
  form.sailors = sailorMinimum.value
  form.soldiers = 0
  form.musketeers = 0
  form.mercenaries = 0
}

function resetSlots() {
  for (const fieldName of Object.keys(slotLimits)) {
    form[fieldName] = slotLimitForField(fieldName) > 0 ? [emptyInventorySlot()] : []
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
    special_crew_slots: normalizeInventorySlots(form.special_crew_slots),
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
    const created = await createBuild(buildPayload())
    await router.push(`/builds/${created.id}`)
  } catch (err) {
    error.value = err.message || t('builds.create.saveError')
  } finally {
    saving.value = false
  }
}

let optionRequestId = 0
watch(
  () => form.ship_id,
  async (shipId) => {
    setCrewToShipMinimum()
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

watch(sailorMinimum, (minimum) => {
  if (Number(form.sailors) < minimum) {
    form.sailors = minimum
  }
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
    form.ship_id = ships.value[0]?.id || ''
    optionCatalog.value = await getBuildOptions(form.ship_id || null)
    resetSlots()
    setCrewToShipMinimum()
  } catch (err) {
    error.value = err.message || t('builds.create.loadError')
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
          <h1 id="build-create-title">{{ t('builds.create.title') }}</h1>
          <p>{{ t('builds.create.subtitle') }}</p>
        </div>
        <RouterLink class="small-action" to="/builds">{{ t('common.back') }}</RouterLink>
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
        <div v-if="selectedShip" class="ship-stat-row" :aria-label="t('builds.create.sections.ship')">
          <span>{{ t('builds.create.stats.rate', { value: selectedShip.rate }) }}</span>
          <span>{{ t('builds.create.stats.type', { value: selectedShip.ship_type }) }}</span>
          <span>{{ t('builds.create.stats.durability', { value: selectedShip.durability }) }}</span>
          <span>{{ t('builds.create.stats.speed', { value: selectedShip.speed_knots }) }}</span>
          <span>{{ t('builds.create.stats.crew', { value: selectedShip.crew_capacity }) }}</span>
          <span>{{ t('builds.create.stats.sailorMinimum', { value: selectedShip.sailor_minimum }) }}</span>
          <span>{{ t('builds.create.stats.upgrades', { count: availableUpgradeSlots }) }}</span>
          <span>{{ t('builds.create.stats.weapons', { value: shipStatsPreview.weaponTotal }) }}</span>
          <span>{{ t('builds.create.stats.specialCrew', { value: shipStatsPreview.specialCrew }) }}</span>
        </div>
        <div v-if="selectedShip" class="build-stat-breakdown compact">
          <div class="stat-breakdown-heading">
            <strong>{{ t('builds.stats.breakdownTitle') }}</strong>
            <span>{{ t('builds.stats.breakdownHint') }}</span>
          </div>
          <div class="stat-breakdown-grid">
            <article v-for="row in buildStatRows" :key="row.key" class="stat-breakdown-row" :class="{ 'is-debuff': row.isDebuff, 'has-modifier': Number(row.modifier) !== 0 }">
              <span>{{ row.label }}</span>
              <strong>{{ formatStatValue(row.effective, row.unit, row.precision) }}</strong>
              <small>{{ t('builds.stats.baseAndModifier', { base: formatStatValue(row.base, row.unit, row.precision), modifier: formatModifier(row) }) }}</small>
            </article>
          </div>
        </div>
      </section>

      <section class="wire-section form-section equipment-section" :aria-label="t('builds.create.sections.equipment')">
        <div class="section-title">
          <span>03</span>
          <h2>{{ t('builds.create.sections.equipment') }}</h2>
        </div>
        <div class="equipment-unified-grid">
          <label class="square-slot equipment-slot equipment-slot-sail">
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.sail') }}</span>
            <span class="select-shell">
              <select v-model="form.sails" :aria-label="t('builds.create.equipment.sail')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('sail')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>

          <label v-for="index in equipmentUpgradeCount" :key="index" class="square-slot equipment-slot equipment-slot-upgrade">
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
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
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.lantern') }}</span>
            <span class="select-shell">
              <select v-model="form.lantern" :aria-label="t('builds.create.equipment.lantern')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('lantern')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>
        </div>
      </section>

      <section class="wire-section form-section weapons-section" :aria-label="t('builds.create.sections.weapons')">
        <div class="section-title">
          <span>04</span>
          <h2>{{ t('builds.create.sections.weapons') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('builds.create.weapons.hint') }}</p>
        <div class="inventory-grid weapon-arc-grid five-columns">
          <div v-for="arc in availableWeaponArcs" :key="arc.fieldName" class="inventory-panel weapon-arc-panel">
            <div class="inventory-heading">
              <strong>{{ t(arc.labelKey) }}</strong>
              <span>{{ t('builds.create.weapons.capacity', { count: slotQuantityTotal(arc.fieldName), max: weaponCapacityForField(arc.fieldName) }) }}</span>
            </div>
            <p v-if="isWeaponFieldUnavailable(arc.fieldName)" class="slot-hint">{{ t('builds.create.weapons.unavailable') }}</p>
            <label v-for="(slot, index) in form[arc.fieldName]" :key="`${arc.fieldName}-${index}`" class="inventory-slot-select with-quantity" :class="{ 'is-invalid': weaponSelectionInvalid(arc.fieldName, slot.item) || weaponFieldOverCapacity(arc.fieldName) }">
              <span class="slot-image-cell">
                <img :src="slotPlaceholderSrc" :alt="t(arc.altKey, { index: index + 1 })" />
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
                :max="weaponCapacityForField(arc.fieldName) || 999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange(arc.fieldName, index, $event)"
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
              <span>{{ t('builds.create.inventory.limitedSlotCount', { count: slotCount('special_crew_slots'), max: 8 }) }}</span>
            </div>
            <label v-for="(slot, index) in form.special_crew_slots" :key="`special-crew-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.specialCrew.alt', { index: index + 1 })" />
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
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('special_crew_slots', index, $event)"
              />
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section crew-section" :aria-label="t('builds.create.sections.crew')">
        <div class="section-title">
          <span>06</span>
          <h2>{{ t('builds.create.sections.crew') }}</h2>
        </div>
        <div class="crew-status" :class="{ 'is-invalid': crewInvalid }">
          <span>{{ t('builds.create.crew.total', { current: crewTotal, max: crewCapacity || '—' }) }}</span>
          <span>{{ t('builds.create.crew.free', { value: crewRemaining }) }}</span>
          <span>{{ t('builds.create.crew.sailorMinimum', { value: sailorMinimum }) }}</span>
          <span v-if="sailorsBelowMinimum">· {{ t('builds.create.crew.tooFewSailors') }}</span>
          <span v-else-if="crewOverLimit">· {{ t('builds.create.crew.tooManyCrew') }}</span>
        </div>

        <div class="crew-grid section-fields">
          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.sailors') }} <strong>{{ form.sailors }}</strong></span>
            <input v-model.number="form.sailors" type="range" :min="sailorMinimum" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.musketeers') }} <strong>{{ form.musketeers }}</strong></span>
            <input v-model.number="form.musketeers" type="range" min="0" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.soldiers') }} <strong>{{ form.soldiers }}</strong></span>
            <input v-model.number="form.soldiers" type="range" min="0" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.mercenaries') }} <strong>{{ form.mercenaries }}</strong></span>
            <input v-model.number="form.mercenaries" type="range" min="0" :max="crewCapacity" />
          </label>
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
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.ammunitionAlt', { index: index + 1 })" />
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
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.consumableAlt', { index: index + 1 })" />
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
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.holdAlt', { index: index + 1 })" />
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

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="form-actions">
        <RouterLink class="wire-section form-button" to="/builds">{{ t('common.cancel') }}</RouterLink>
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving ? t('builds.create.saving') : t('builds.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
