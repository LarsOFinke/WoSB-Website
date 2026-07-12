<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import {
  createMasterDataCategory,
  createMasterDataOption,
  createMasterDataShip,
  deactivateMasterDataCategory,
  deactivateMasterDataOption,
  deactivateMasterDataShip,
  getMasterDataOverview,
  getMasterDataTaxonomy,
  listMasterDataCategories,
  listMasterDataOptions,
  listMasterDataShips,
  restoreMasterDataCategory,
  restoreMasterDataOption,
  restoreMasterDataShip,
  updateMasterDataCategory,
  updateMasterDataOption,
  updateMasterDataShip,
} from '@/modules/admin/api/admin'
import { absoluteFileUrl, IMAGE_MIME_TYPES } from '@/modules/files/api/files'

const { t } = useLocale()

const activeTab = ref('ships')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const overview = ref({ category_count: 0, option_count: 0, ship_count: 0, overridden_count: 0, inactive_count: 0 })
const taxonomy = ref({ weapon_classes: [], weapon_slot_types: [] })
const categories = ref([])
const options = ref([])
const upgradeOptions = ref([])
const ships = ref([])
const optionCategory = ref('')
const optionSearch = ref('')
const shipSearch = ref('')
let optionSearchTimer = null
let shipSearchTimer = null

const categoryEditingId = ref(null)
const optionEditingId = ref(null)
const shipEditingId = ref(null)
const effectsText = ref('{}')

const categoryForm = reactive({ key: '', label: '', sort_order: 100, is_active: true })
const optionForm = reactive({
  category_id: '',
  name: '',
  source: '',
  notes: '',
  image_url: '',
  option_kind: '',
  weapon_class: '',
  weapon_caliber_inches: '',
  allowed_slot_types: [],
  sort_order: 100,
  is_active: true,
})
const shipForm = reactive({
  name: '',
  rate: 7,
  ship_type: 'Ship',
  durability: 0,
  speed_knots: 0,
  maneuverability: 0,
  armor: 0,
  hold_capacity: 0,
  crew_capacity: 100,
  sailor_minimum: 0,
  displacement_tons: 0,
  source: '',
  image_url: '',
  sail_slots: 1,
  upgrade_slots: 5,
  has_lantern: true,
  is_active: true,
  weapon_mounts: [],
  upgrade_effect_overrides: [],
})

const selectedOption = computed(() => options.value.find((row) => row.id === optionEditingId.value))
const selectedShip = computed(() => ships.value.find((row) => row.id === shipEditingId.value))

const tabCounts = computed(() => ({
  options: overview.value.option_count,
  ships: overview.value.ship_count,
  categories: overview.value.category_count,
}))

function seedStatusClass(row) {
  return `status-${row?.seed_status || 'custom'}`
}

function mountLabel(slotType) {
  return taxonomy.value.weapon_slot_types.find((row) => row.code === slotType)?.label || slotType
}

function visibleMounts(mounts = []) {
  return mounts.filter((mount) => Number(mount.capacity || 0) > 0)
}

function seedStatusLabel(row) {
  return t(`masterData.seedStatus.${row?.seed_status || 'custom'}`)
}

function clearMessages() {
  error.value = ''
  success.value = ''
}

function imagePreview(url) {
  return absoluteFileUrl(url)
}

function applyUploadedImage(form, file) {
  clearMessages()
  if (!String(file?.mime_type || '').startsWith('image/')) {
    error.value = t('files.validation.unsupportedType', { name: file?.original_name || '' })
    return
  }
  form.image_url = file.public_url
}

function blankMounts(rows = []) {
  const current = new Map(rows.map((row) => [row.slot_type, row]))
  return taxonomy.value.weapon_slot_types.map((slot) => ({
    slot_type: slot.code,
    capacity: Number(current.get(slot.code)?.capacity || 0),
    max_weapon_class: current.get(slot.code)?.max_weapon_class || '',
    max_caliber_inches: current.get(slot.code)?.max_caliber_inches ?? '',
  }))
}

function resetCategory(row = null) {
  categoryEditingId.value = row?.id || null
  categoryForm.key = row?.key || ''
  categoryForm.label = row?.label || ''
  categoryForm.sort_order = row?.sort_order ?? 100
  categoryForm.is_active = row?.is_active ?? true
  clearMessages()
}

function resetOption(row = null) {
  optionEditingId.value = row?.id || null
  optionForm.category_id = row?.category_id || categories.value[0]?.id || ''
  optionForm.name = row?.name || ''
  optionForm.source = row?.source || ''
  optionForm.notes = row?.notes || ''
  optionForm.image_url = row?.image_url || ''
  optionForm.option_kind = row?.option_kind || ''
  optionForm.weapon_class = row?.weapon_class || ''
  optionForm.weapon_caliber_inches = row?.weapon_caliber_inches ?? ''
  optionForm.allowed_slot_types = [...(row?.allowed_slot_types || [])]
  optionForm.sort_order = row?.sort_order ?? 100
  optionForm.is_active = row?.is_active ?? true
  effectsText.value = JSON.stringify(row?.stat_effects || {}, null, 2)
  clearMessages()
}

function resetShip(row = null) {
  shipEditingId.value = row?.id || null
  shipForm.name = row?.name || ''
  shipForm.rate = row?.rate ?? 7
  shipForm.ship_type = row?.ship_type || 'Ship'
  shipForm.durability = row?.durability ?? 0
  shipForm.speed_knots = row?.speed_knots ?? 0
  shipForm.maneuverability = row?.maneuverability ?? 0
  shipForm.armor = row?.armor ?? 0
  shipForm.hold_capacity = row?.hold_capacity ?? 0
  shipForm.crew_capacity = row?.crew_capacity ?? 100
  shipForm.sailor_minimum = row?.sailor_minimum ?? 0
  shipForm.displacement_tons = row?.displacement_tons ?? 0
  shipForm.source = row?.source || ''
  shipForm.image_url = row?.image_url || ''
  shipForm.sail_slots = row?.sail_slots ?? 1
  shipForm.upgrade_slots = row?.upgrade_slots ?? 5
  shipForm.has_lantern = row?.has_lantern ?? true
  shipForm.is_active = row?.is_active ?? true
  shipForm.weapon_mounts = blankMounts(row?.weapon_mounts || [])
  shipForm.upgrade_effect_overrides = (row?.upgrade_effect_overrides || []).map((override) => ({
    option_id: override.option_id,
    effects_text: JSON.stringify(override.stat_effects || {}, null, 2),
  }))
  clearMessages()
}

async function loadOverview() {
  overview.value = await getMasterDataOverview()
}

async function loadCategories() {
  categories.value = await listMasterDataCategories()
  if (!optionForm.category_id) optionForm.category_id = categories.value[0]?.id || ''
}

async function loadOptions() {
  options.value = await listMasterDataOptions({ category: optionCategory.value, search: optionSearch.value })
}

async function loadUpgradeOptions() {
  upgradeOptions.value = await listMasterDataOptions({ category: 'upgrade' })
}

async function loadShips() {
  ships.value = await listMasterDataShips(shipSearch.value)
}

async function reloadAll() {
  loading.value = true
  error.value = ''
  try {
    const [overviewRows, taxonomyRows, categoryRows] = await Promise.all([
      getMasterDataOverview(),
      getMasterDataTaxonomy(),
      listMasterDataCategories(),
    ])
    overview.value = overviewRows
    taxonomy.value = taxonomyRows
    categories.value = categoryRows
    await Promise.all([loadOptions(), loadUpgradeOptions(), loadShips()])
    if (!shipForm.weapon_mounts.length) shipForm.weapon_mounts = blankMounts()
  } catch (err) {
    error.value = err.message || t('masterData.loadError')
  } finally {
    loading.value = false
  }
}

async function saveCategory() {
  clearMessages()
  saving.value = true
  try {
    const payload = {
      label: categoryForm.label,
      sort_order: Number(categoryForm.sort_order),
      is_active: categoryForm.is_active,
    }
    if (categoryEditingId.value) {
      await updateMasterDataCategory(categoryEditingId.value, payload)
    } else {
      await createMasterDataCategory({ ...payload, key: categoryForm.key })
    }
    await Promise.all([loadCategories(), loadOverview()])
    resetCategory()
    success.value = t('masterData.saved')
  } catch (err) {
    error.value = err.message || t('masterData.saveError')
  } finally {
    saving.value = false
  }
}

function parseEffects() {
  const parsed = JSON.parse(effectsText.value || '{}')
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(t('masterData.effectsError'))
  return parsed
}

async function saveOption() {
  clearMessages()
  saving.value = true
  try {
    const payload = {
      category_id: Number(optionForm.category_id),
      name: optionForm.name,
      source: optionForm.source || null,
      notes: optionForm.notes || null,
      image_url: optionForm.image_url || null,
      option_kind: optionForm.option_kind || null,
      weapon_class: optionForm.weapon_class || null,
      weapon_caliber_inches: optionForm.weapon_caliber_inches === '' ? null : Number(optionForm.weapon_caliber_inches),
      stat_effects: parseEffects(),
      allowed_slot_types: [...optionForm.allowed_slot_types],
      sort_order: Number(optionForm.sort_order),
      is_active: optionForm.is_active,
    }
    if (optionEditingId.value) {
      await updateMasterDataOption(optionEditingId.value, payload)
    } else {
      await createMasterDataOption(payload)
    }
    await Promise.all([loadOptions(), loadOverview()])
    resetOption()
    success.value = t('masterData.saved')
  } catch (err) {
    error.value = err.message || t('masterData.saveError')
  } finally {
    saving.value = false
  }
}

function upgradeOptionById(optionId) {
  return upgradeOptions.value.find((row) => row.id === Number(optionId))
}

function upgradeChoicesForOverride(index) {
  const current = Number(shipForm.upgrade_effect_overrides[index]?.option_id || 0)
  const selected = new Set(shipForm.upgrade_effect_overrides.map((row) => Number(row.option_id)).filter(Boolean))
  return upgradeOptions.value.filter((row) => row.id === current || !selected.has(row.id))
}

function addUpgradeOverride() {
  const selected = new Set(shipForm.upgrade_effect_overrides.map((row) => Number(row.option_id)).filter(Boolean))
  const option = upgradeOptions.value.find((row) => !selected.has(row.id))
  if (!option) return
  shipForm.upgrade_effect_overrides.push({ option_id: option.id, effects_text: '{}' })
}

function removeUpgradeOverride(index) {
  shipForm.upgrade_effect_overrides.splice(index, 1)
}

function parseShipUpgradeOverrides() {
  return shipForm.upgrade_effect_overrides.map((row) => {
    const parsed = JSON.parse(row.effects_text || '{}')
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(t('masterData.effectsError'))
    return { option_id: Number(row.option_id), stat_effects: parsed }
  })
}

async function saveShip() {
  clearMessages()
  saving.value = true
  try {
    const payload = {
      ...shipForm,
      rate: Number(shipForm.rate),
      durability: Number(shipForm.durability),
      speed_knots: Number(shipForm.speed_knots),
      maneuverability: Number(shipForm.maneuverability),
      armor: Number(shipForm.armor),
      hold_capacity: Number(shipForm.hold_capacity),
      crew_capacity: Number(shipForm.crew_capacity),
      sailor_minimum: Number(shipForm.sailor_minimum),
      displacement_tons: Number(shipForm.displacement_tons),
      sail_slots: Number(shipForm.sail_slots),
      upgrade_slots: Number(shipForm.upgrade_slots),
      source: shipForm.source || null,
      image_url: shipForm.image_url || null,
      upgrade_effect_overrides: parseShipUpgradeOverrides(),
      weapon_mounts: shipForm.weapon_mounts.map((mount) => ({
        slot_type: mount.slot_type,
        capacity: Number(mount.capacity || 0),
        max_weapon_class: mount.max_weapon_class || null,
        max_caliber_inches: mount.max_caliber_inches === '' ? null : Number(mount.max_caliber_inches),
      })),
    }
    if (shipEditingId.value) {
      await updateMasterDataShip(shipEditingId.value, payload)
    } else {
      await createMasterDataShip(payload)
    }
    await Promise.all([loadShips(), loadOverview()])
    resetShip()
    success.value = t('masterData.saved')
  } catch (err) {
    error.value = err.message || t('masterData.saveError')
  } finally {
    saving.value = false
  }
}

async function runRecordAction(action, reload, reset) {
  clearMessages()
  saving.value = true
  try {
    await action()
    await Promise.all([reload(), loadOverview()])
    reset?.()
    success.value = t('masterData.saved')
  } catch (err) {
    error.value = err.message || t('masterData.saveError')
  } finally {
    saving.value = false
  }
}

async function deactivateCategory(row) {
  await runRecordAction(
    () => deactivateMasterDataCategory(row.id),
    loadCategories,
    categoryEditingId.value === row.id ? () => resetCategory() : null,
  )
}

async function deactivateOption(row) {
  await runRecordAction(
    () => deactivateMasterDataOption(row.id),
    loadOptions,
    optionEditingId.value === row.id ? () => resetOption() : null,
  )
}

async function deactivateShip(row) {
  await runRecordAction(
    () => deactivateMasterDataShip(row.id),
    loadShips,
    shipEditingId.value === row.id ? () => resetShip() : null,
  )
}

async function restoreCategory(row) {
  await runRecordAction(() => restoreMasterDataCategory(row.id), loadCategories, () => resetCategory())
}

async function restoreOption(row) {
  await runRecordAction(() => restoreMasterDataOption(row.id), loadOptions, () => resetOption())
}

async function restoreShip(row) {
  await runRecordAction(() => restoreMasterDataShip(row.id), loadShips, () => resetShip())
}

watch([optionCategory, optionSearch], () => {
  window.clearTimeout(optionSearchTimer)
  optionSearchTimer = window.setTimeout(loadOptions, 180)
})
watch(shipSearch, () => {
  window.clearTimeout(shipSearchTimer)
  shipSearchTimer = window.setTimeout(loadShips, 180)
})

onMounted(reloadAll)
</script>

<template>
  <section class="master-data-page" aria-labelledby="master-data-title">
    <div class="wire-frame page-frame master-data-frame">
      <PageHeader
        :eyebrow="t('masterData.eyebrow')"
        :title="t('masterData.title')"
        :description="t('masterData.subtitle')"
        title-id="master-data-title"
      >
        <template #actions>
          <RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink>
        </template>
      </PageHeader>

      <section class="master-data-metrics" aria-label="Master data summary">
        <MetricCard :label="t('masterData.metrics.categories')" :value="overview.category_count" />
        <MetricCard :label="t('masterData.metrics.options')" :value="overview.option_count" />
        <MetricCard :label="t('masterData.metrics.ships')" :value="overview.ship_count" />
        <MetricCard :label="t('masterData.metrics.overrides')" :value="overview.overridden_count" tone="warning" />
        <MetricCard :label="t('masterData.metrics.inactive')" :value="overview.inactive_count" />
      </section>

      <nav class="master-data-tabs" aria-label="Master data catalogs">
        <button
          v-for="tab in ['ships', 'options', 'categories']"
          :key="tab"
          type="button"
          class="catalog-tab"
          :class="{ 'is-active': activeTab === tab }"
          :aria-pressed="activeTab === tab"
          @click="activeTab = tab"
        >
          <span>{{ t(`masterData.tabs.${tab}`) }}</span>
          <strong>{{ tabCounts[tab] }}</strong>
        </button>
      </nav>

      <div v-if="loading || error || success" class="master-data-notices" aria-live="polite">
        <p v-if="loading" class="notice-card muted">{{ t('masterData.loading') }}</p>
        <p v-if="error" class="notice-card error-text">{{ error }}</p>
        <p v-if="success" class="notice-card success-text">{{ success }}</p>
      </div>

      <section v-if="activeTab === 'categories'" class="master-data-workspace">
        <aside class="catalog-panel">
          <header class="catalog-panel-header">
            <div>
              <span class="panel-kicker">{{ categories.length }}</span>
              <h2>{{ t('masterData.categories.title') }}</h2>
            </div>
            <button class="small-action" type="button" @click="resetCategory()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-scroll">
            <article
              v-for="row in categories"
              :key="row.id"
              class="catalog-record"
              :class="[seedStatusClass(row), { 'is-selected': categoryEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetCategory(row)">
                <span class="record-icon">#</span>
                <span class="record-copy"><strong>{{ row.label }}</strong><small>{{ row.key }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreCategory(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateCategory(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel" @submit.prevent="saveCategory">
          <header class="editor-header">
            <div><span class="panel-kicker">{{ categoryEditingId ? seedStatusLabel(categories.find((row) => row.id === categoryEditingId)) : t('masterData.customRecord') }}</span><h2>{{ categoryEditingId ? t('masterData.categories.edit') : t('masterData.categories.create') }}</h2></div>
          </header>
          <div class="editor-section form-grid two-columns">
            <label><span>{{ t('masterData.fields.key') }}</span><input v-model="categoryForm.key" required maxlength="40" :disabled="Boolean(categoryEditingId)" /></label>
            <label><span>{{ t('masterData.fields.label') }}</span><input v-model="categoryForm.label" required maxlength="80" /></label>
            <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="categoryForm.sort_order" type="number" min="0" /></label>
            <label class="toggle-field"><input v-model="categoryForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label>
          </div>
          <footer class="editor-actions"><button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button></footer>
        </form>
      </section>

      <section v-if="activeTab === 'options'" class="master-data-workspace">
        <aside class="catalog-panel">
          <header class="catalog-panel-header">
            <div><span class="panel-kicker">{{ options.length }}</span><h2>{{ t('masterData.options.title') }}</h2></div>
            <button class="small-action" type="button" @click="resetOption()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-toolbar">
            <select v-model="optionCategory"><option value="">{{ t('masterData.allCategories') }}</option><option v-for="row in categories" :key="row.id" :value="row.key">{{ row.label }}</option></select>
            <input v-model="optionSearch" type="search" :placeholder="t('common.search')" />
          </div>
          <div class="catalog-scroll">
            <article
              v-for="row in options"
              :key="row.id"
              class="catalog-record"
              :class="[seedStatusClass(row), { 'is-selected': optionEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetOption(row)">
                <span class="record-image"><img v-if="row.image_url" :src="imagePreview(row.image_url)" alt="" /><span v-else>✦</span></span>
                <span class="record-copy"><strong>{{ row.name }}</strong><small>{{ row.category_label }} · {{ row.option_kind || '—' }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreOption(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateOption(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel" @submit.prevent="saveOption">
          <header class="editor-header editor-header-with-preview">
            <div class="editor-preview"><img v-if="optionForm.image_url" :src="imagePreview(optionForm.image_url)" alt="" /><span v-else>✦</span></div>
            <div><span class="panel-kicker">{{ selectedOption ? seedStatusLabel(selectedOption) : t('masterData.customRecord') }}</span><h2>{{ optionEditingId ? t('masterData.options.edit') : t('masterData.options.create') }}</h2><p>{{ optionForm.name || '—' }}</p></div>
          </header>
          <div v-if="selectedOption" class="seed-note"><strong>{{ seedStatusLabel(selectedOption) }}</strong><span>{{ selectedOption.seed_status === 'custom' ? t('masterData.customRecord') : selectedOption.seed_revision }}</span></div>

          <fieldset class="editor-section"><legend>{{ t('masterData.options.title') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.category') }}</span><select v-model="optionForm.category_id" required><option v-for="row in categories" :key="row.id" :value="row.id">{{ row.label }}</option></select></label>
              <label><span>{{ t('masterData.fields.name') }}</span><input v-model="optionForm.name" required maxlength="160" /></label>
              <label><span>{{ t('masterData.fields.kind') }}</span><input v-model="optionForm.option_kind" maxlength="40" /></label>
              <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="optionForm.sort_order" type="number" min="0" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.weaponMounts') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="optionForm.weapon_class"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label>
              <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="optionForm.weapon_caliber_inches" type="number" min="0" step="0.1" /></label>
            </div>
            <div class="choice-grid"><label v-for="row in taxonomy.weapon_slot_types" :key="row.code" class="choice-card"><input v-model="optionForm.allowed_slot_types" type="checkbox" :value="row.code" /><span>{{ row.label }}</span></label></div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.effects') }}</legend>
            <label><textarea v-model="effectsText" rows="8" spellcheck="false"></textarea><small>{{ t('masterData.effectsHint') }}</small></label>
          </fieldset>

          <fieldset class="editor-section upgrade-override-section"><legend>{{ t('masterData.shipUpgradeOverrides.title') }}</legend>
            <p class="section-description">{{ t('masterData.shipUpgradeOverrides.hint') }}</p>
            <div v-if="shipForm.upgrade_effect_overrides.length" class="upgrade-override-list">
              <article v-for="(override, index) in shipForm.upgrade_effect_overrides" :key="`upgrade-override-${index}`" class="upgrade-override-card">
                <div class="override-card-header">
                  <label><span>{{ t('masterData.shipUpgradeOverrides.upgrade') }}</span><select v-model.number="override.option_id"><option v-for="row in upgradeChoicesForOverride(index)" :key="row.id" :value="row.id">{{ row.name }}</option></select></label>
                  <button class="danger-action" type="button" @click="removeUpgradeOverride(index)">{{ t('masterData.shipUpgradeOverrides.remove') }}</button>
                </div>
                <div class="override-effect-grid">
                  <div><span>{{ t('masterData.shipUpgradeOverrides.defaultEffects') }}</span><pre>{{ JSON.stringify(upgradeOptionById(override.option_id)?.stat_effects || {}, null, 2) }}</pre></div>
                  <label><span>{{ t('masterData.shipUpgradeOverrides.overrideEffects') }}</span><textarea v-model="override.effects_text" rows="5" spellcheck="false"></textarea></label>
                </div>
              </article>
            </div>
            <p v-else class="empty-state-inline">{{ t('masterData.shipUpgradeOverrides.empty') }}</p>
            <button class="small-action add-override-button" type="button" :disabled="shipForm.upgrade_effect_overrides.length >= upgradeOptions.length" @click="addUpgradeOverride">{{ t('masterData.shipUpgradeOverrides.add') }}</button>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.source') }}</legend>
            <div class="form-grid">
              <label><span>{{ t('masterData.fields.source') }}</span><input v-model="optionForm.source" maxlength="240" /></label>
              <label><span>{{ t('masterData.fields.notes') }}</span><textarea v-model="optionForm.notes" rows="3" maxlength="500"></textarea></label>
              <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="optionForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
            </div>
            <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(optionForm, $event)" />
          </fieldset>

          <footer class="editor-actions"><label class="toggle-field"><input v-model="optionForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label><button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button></footer>
        </form>
      </section>

      <section v-if="activeTab === 'ships'" class="master-data-workspace">
        <aside class="catalog-panel ship-catalog-panel">
          <header class="catalog-panel-header">
            <div><span class="panel-kicker">{{ ships.length }}</span><h2>{{ t('masterData.ships.title') }}</h2></div>
            <button class="small-action" type="button" @click="resetShip()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-toolbar single"><input v-model="shipSearch" type="search" :placeholder="t('common.search')" /></div>
          <div class="catalog-scroll">
            <article
              v-for="row in ships"
              :key="row.id"
              class="catalog-record ship-record"
              :class="[seedStatusClass(row), { 'is-selected': shipEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetShip(row)">
                <span class="record-image ship-record-image"><img v-if="row.image_url" :src="imagePreview(row.image_url)" alt="" /><span v-else>⚓</span></span>
                <span class="record-copy"><strong>{{ row.name }}</strong><small>{{ t('common.rate') }} {{ row.rate }} · {{ row.ship_type }}</small><small class="weapon-layout">{{ row.weapon_layout }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreShip(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateShip(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel ship-editor" @submit.prevent="saveShip">
          <header class="editor-header editor-header-with-preview ship-editor-header">
            <div class="editor-preview ship-editor-preview"><img v-if="shipForm.image_url" :src="imagePreview(shipForm.image_url)" alt="" /><span v-else>⚓</span></div>
            <div><span class="panel-kicker">{{ selectedShip ? seedStatusLabel(selectedShip) : t('masterData.customRecord') }}</span><h2>{{ shipForm.name || (shipEditingId ? t('masterData.ships.edit') : t('masterData.ships.create')) }}</h2><p>{{ t('common.rate') }} {{ shipForm.rate }} · {{ shipForm.ship_type || '—' }}</p></div>
            <div class="ship-quick-stats"><span><small>{{ t('masterData.fields.durability') }}</small><strong>{{ shipForm.durability }}</strong></span><span><small>{{ t('masterData.fields.speed') }}</small><strong>{{ shipForm.speed_knots }}</strong></span><span><small>{{ t('masterData.fields.crewCapacity') }}</small><strong>{{ shipForm.crew_capacity }}</strong></span></div>
          </header>
          <div v-if="selectedShip" class="seed-note"><strong>{{ seedStatusLabel(selectedShip) }}</strong><span>{{ selectedShip.seed_status === 'custom' ? t('masterData.customRecord') : selectedShip.seed_revision }}</span></div>

          <fieldset class="editor-section"><legend>{{ t('masterData.ships.title') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.name') }}</span><input v-model="shipForm.name" required maxlength="120" /></label>
              <label><span>{{ t('masterData.fields.type') }}</span><input v-model="shipForm.ship_type" required maxlength="80" /></label>
            </div>
            <div class="form-grid three-columns compact-fields">
              <label><span>{{ t('common.rate') }}</span><input v-model.number="shipForm.rate" type="number" min="1" max="7" /></label>
              <label><span>{{ t('masterData.fields.sailSlots') }}</span><input v-model.number="shipForm.sail_slots" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.upgradeSlots') }}</span><input v-model.number="shipForm.upgrade_slots" type="number" min="0" max="7" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.durability') }}</legend>
            <div class="form-grid three-columns">
              <label><span>{{ t('masterData.fields.durability') }}</span><input v-model.number="shipForm.durability" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.speed') }}</span><input v-model.number="shipForm.speed_knots" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.maneuverability') }}</span><input v-model.number="shipForm.maneuverability" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.armor') }}</span><input v-model.number="shipForm.armor" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.holdCapacity') }}</span><input v-model.number="shipForm.hold_capacity" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.displacement') }}</span><input v-model.number="shipForm.displacement_tons" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.crewCapacity') }}</span><input v-model.number="shipForm.crew_capacity" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.sailorMinimum') }}</span><input v-model.number="shipForm.sailor_minimum" type="number" min="0" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section mount-section"><legend>{{ t('masterData.fields.weaponMounts') }}</legend>
            <div v-if="visibleMounts(shipForm.weapon_mounts).length" class="mount-summary">
              <span v-for="mount in visibleMounts(shipForm.weapon_mounts)" :key="`summary-${mount.slot_type}`"><small>{{ mountLabel(mount.slot_type) }}</small><strong>{{ mount.capacity }}</strong></span>
            </div>
            <div class="mount-grid">
              <div v-for="mount in shipForm.weapon_mounts" :key="mount.slot_type" class="mount-card" :class="{ 'has-capacity': Number(mount.capacity || 0) > 0 }">
                <strong>{{ mountLabel(mount.slot_type) }}</strong>
                <label><span>{{ t('masterData.fields.capacity') }}</span><input v-model.number="mount.capacity" type="number" min="0" /></label>
                <label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="mount.max_weapon_class"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label>
                <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="mount.max_caliber_inches" type="number" min="0" step="0.1" /></label>
              </div>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.source') }}</legend>
            <div class="form-grid">
              <label><span>{{ t('masterData.fields.source') }}</span><input v-model="shipForm.source" maxlength="240" /></label>
              <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="shipForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
            </div>
            <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(shipForm, $event)" />
          </fieldset>

          <footer class="editor-actions">
            <div class="editor-toggles"><label class="toggle-field"><input v-model="shipForm.has_lantern" type="checkbox" /><span>{{ t('masterData.fields.lantern') }}</span></label><label class="toggle-field"><input v-model="shipForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label></div>
            <button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button>
          </footer>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.master-data-frame { gap: clamp(1rem, 1.8vw, 1.45rem); }
.master-data-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .75rem; }
.master-data-tabs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .7rem; padding: .45rem; border: 1px solid var(--line); border-radius: var(--radius-lg); background: rgba(8, 17, 27, .58); }
.catalog-tab { min-height: 3.65rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: .75rem 1rem; border: 1px solid transparent; border-radius: var(--radius-md); color: var(--muted); background: transparent; cursor: pointer; font-weight: 850; }
.catalog-tab strong { min-width: 2.1rem; padding: .18rem .5rem; border-radius: var(--radius-pill); color: var(--text); background: rgba(255,255,255,.07); text-align: center; }
.catalog-tab:hover { color: var(--text); background: rgba(255,255,255,.045); }
.catalog-tab.is-active { color: var(--accent-strong); border-color: rgba(241,184,91,.34); background: linear-gradient(135deg, rgba(241,184,91,.15), rgba(255,255,255,.035)); box-shadow: inset 0 1px 0 rgba(255,255,255,.05); }
.master-data-notices { display: grid; gap: .5rem; }
.notice-card { margin: 0; padding: .85rem 1rem; border: 1px solid var(--line); border-radius: var(--radius-md); background: rgba(16,29,43,.82); }
.master-data-workspace { display: grid; grid-template-columns: minmax(340px, .82fr) minmax(560px, 1.18fr); gap: 1rem; align-items: start; min-width: 0; }
.catalog-panel, .editor-panel { min-width: 0; border: 1px solid var(--line); border-radius: var(--radius-lg); background: linear-gradient(180deg, rgba(20,35,53,.88), rgba(11,21,32,.9)); box-shadow: var(--shadow-soft); overflow: hidden; }
.catalog-panel { position: sticky; top: 6.2rem; display: grid; grid-template-rows: auto auto minmax(0, 1fr); max-height: calc(100vh - 7.5rem); }
.catalog-panel-header, .editor-header, .editor-actions { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem 1.1rem; }
.catalog-panel-header { border-bottom: 1px solid var(--line); background: rgba(255,255,255,.025); }
.catalog-panel-header h2, .editor-header h2 { margin: .08rem 0 0; font-size: clamp(1.15rem, 1.8vw, 1.45rem); }
.panel-kicker { color: var(--accent); font-size: .72rem; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; }
.catalog-toolbar { display: grid; grid-template-columns: minmax(130px, .8fr) minmax(160px, 1.2fr); gap: .55rem; padding: .75rem; border-bottom: 1px solid var(--line); background: rgba(8,17,27,.45); }
.catalog-toolbar.single { grid-template-columns: 1fr; }
.catalog-toolbar input, .catalog-toolbar select, .editor-panel input, .editor-panel select, .editor-panel textarea { width: 100%; min-width: 0; padding: .72rem .8rem; border: 1px solid rgba(221,231,244,.18); border-radius: var(--radius-sm); color: var(--text); background: rgba(5,12,19,.56); }
.catalog-toolbar input:focus, .catalog-toolbar select:focus, .editor-panel input:focus, .editor-panel select:focus, .editor-panel textarea:focus { border-color: rgba(241,184,91,.55); box-shadow: 0 0 0 3px rgba(241,184,91,.09); }
.catalog-scroll { min-height: 10rem; overflow: auto; padding: .55rem; scrollbar-gutter: stable; }
.catalog-record { position: relative; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .55rem; align-items: center; margin-bottom: .45rem; padding: .55rem; border: 1px solid transparent; border-radius: var(--radius-md); background: rgba(255,255,255,.025); }
.catalog-record::before { content: ''; position: absolute; inset: .65rem auto .65rem 0; width: 3px; border-radius: 0 3px 3px 0; background: rgba(184,196,210,.35); }
.catalog-record.status-seeded::before { background: var(--success); }
.catalog-record.status-overridden::before { background: var(--accent); }
.catalog-record.status-custom::before { background: #8eb8ee; }
.catalog-record:hover { border-color: rgba(221,231,244,.16); background: rgba(255,255,255,.045); }
.catalog-record.is-selected { border-color: rgba(241,184,91,.48); background: var(--accent-soft); box-shadow: inset 0 0 0 1px rgba(241,184,91,.12); }
.catalog-record.is-inactive { opacity: .58; }
.catalog-record-main { min-width: 0; display: grid; grid-template-columns: auto minmax(0,1fr); gap: .75rem; align-items: center; padding: .25rem .35rem; color: inherit; background: transparent; text-align: left; cursor: pointer; }
.record-icon, .record-image { width: 2.65rem; height: 2.65rem; display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto; border: 1px solid rgba(241,184,91,.22); border-radius: .8rem; color: var(--accent-strong); background: rgba(241,184,91,.075); font-weight: 900; overflow: hidden; }
.record-image img { width: 100%; height: 100%; object-fit: contain; }
.ship-record-image { width: 3.15rem; height: 3.15rem; }
.record-copy { min-width: 0; display: grid; gap: .08rem; }
.record-copy strong, .record-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.record-copy small { color: var(--muted-soft); }
.weapon-layout { color: var(--accent) !important; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.record-meta { display: flex; align-items: center; justify-content: flex-end; gap: .4rem; flex-wrap: wrap; }
.status-chip { display: inline-flex; align-items: center; min-height: 1.85rem; padding: .3rem .55rem; border: 1px solid rgba(221,231,244,.14); border-radius: var(--radius-pill); color: var(--muted); background: rgba(255,255,255,.035); font-size: .72rem; font-weight: 850; white-space: nowrap; }
.editor-panel { display: grid; gap: 0; }
.editor-header { min-height: 5.8rem; border-bottom: 1px solid var(--line); background: radial-gradient(circle at 85% 0%, rgba(241,184,91,.13), transparent 16rem), rgba(255,255,255,.025); }
.editor-header p { margin: .2rem 0 0; color: var(--muted); }
.editor-header-with-preview { justify-content: flex-start; }
.editor-preview { width: 4rem; height: 4rem; display: flex; align-items: center; justify-content: center; flex: 0 0 auto; border: 1px solid rgba(241,184,91,.34); border-radius: 1rem; color: var(--accent-strong); background: rgba(241,184,91,.08); font-size: 1.45rem; overflow: hidden; }
.editor-preview img { width: 100%; height: 100%; object-fit: contain; }
.ship-editor-preview { width: 5.1rem; height: 5.1rem; }
.ship-quick-stats { margin-left: auto; display: grid; grid-template-columns: repeat(3, minmax(70px,1fr)); gap: .45rem; }
.ship-quick-stats span, .mount-summary span { display: grid; gap: .05rem; padding: .48rem .62rem; border: 1px solid rgba(221,231,244,.12); border-radius: .75rem; background: rgba(5,12,19,.38); }
.ship-quick-stats small, .mount-summary small { color: var(--muted-soft); font-size: .68rem; }
.ship-quick-stats strong, .mount-summary strong { color: var(--accent-strong); font-size: .95rem; }
.seed-note { display: flex; justify-content: space-between; gap: 1rem; margin: .85rem 1rem 0; padding: .75rem .85rem; border: 1px solid rgba(241,184,91,.2); border-radius: var(--radius-sm); color: var(--muted); background: rgba(241,184,91,.055); }
.seed-note strong { color: var(--accent-strong); }
.editor-section { min-width: 0; display: grid; gap: .85rem; margin: 1rem 1rem 0; padding: 1rem; border: 1px solid rgba(221,231,244,.12); border-radius: var(--radius-md); background: rgba(5,12,19,.25); }
.editor-section legend { padding: 0 .45rem; color: var(--accent); font-size: .76rem; font-weight: 900; letter-spacing: .08em; text-transform: uppercase; }
.editor-panel label { display: grid; gap: .35rem; min-width: 0; }
.editor-panel label > span { color: var(--muted); font-size: .78rem; font-weight: 750; }
.editor-panel small { color: var(--muted-soft); }
.form-grid { display: grid; gap: .75rem; }
.form-grid.two-columns, .two-columns { grid-template-columns: repeat(2, minmax(0,1fr)); }
.form-grid.three-columns { grid-template-columns: repeat(3, minmax(0,1fr)); }
.choice-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: .5rem; }
.choice-card, .toggle-field { display: flex !important; align-items: center; gap: .55rem; padding: .62rem .7rem; border: 1px solid rgba(221,231,244,.14); border-radius: var(--radius-sm); background: rgba(255,255,255,.025); }
.choice-card input, .toggle-field input { width: auto; flex: 0 0 auto; accent-color: var(--accent); }
.mount-summary { display: flex; gap: .45rem; flex-wrap: wrap; }
.mount-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: .65rem; }
.mount-card { display: grid; grid-template-columns: minmax(100px, .8fr) repeat(3, minmax(85px,1fr)); gap: .55rem; align-items: end; padding: .72rem; border: 1px solid rgba(221,231,244,.1); border-radius: var(--radius-sm); background: rgba(255,255,255,.018); }
.mount-card.has-capacity { border-color: rgba(241,184,91,.24); background: rgba(241,184,91,.045); }
.mount-card > strong { align-self: center; color: var(--text); font-size: .86rem; }
.editor-actions { position: sticky; bottom: 0; z-index: 2; margin-top: 1rem; border-top: 1px solid var(--line); background: rgba(11,21,32,.94); backdrop-filter: blur(14px); }
.editor-toggles { display: flex; gap: .55rem; flex-wrap: wrap; }
.editor-actions .primary-action { min-width: 9rem; }
.section-description { margin: 0; color: var(--muted); line-height: 1.55; }
.upgrade-override-list { display: grid; gap: .75rem; }
.upgrade-override-card { display: grid; gap: .7rem; padding: .8rem; border: 1px solid rgba(241,184,91,.2); border-radius: var(--radius-md); background: rgba(241,184,91,.035); }
.override-card-header { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: .75rem; align-items: end; }
.override-effect-grid { display: grid; grid-template-columns: minmax(0,.8fr) minmax(0,1.2fr); gap: .75rem; }
.override-effect-grid > div { min-width: 0; display: grid; gap: .35rem; }
.override-effect-grid > div > span { color: var(--muted); font-size: .78rem; font-weight: 750; }
.override-effect-grid pre { min-height: 7.6rem; max-height: 14rem; margin: 0; padding: .75rem; overflow: auto; border: 1px solid rgba(221,231,244,.12); border-radius: var(--radius-sm); color: var(--muted); background: rgba(5,12,19,.42); font-size: .75rem; white-space: pre-wrap; }
.empty-state-inline { margin: 0; padding: .8rem; border: 1px dashed rgba(221,231,244,.16); border-radius: var(--radius-sm); color: var(--muted-soft); text-align: center; }
.add-override-button { justify-self: start; }

@media (max-width: 1180px) { .master-data-workspace { grid-template-columns: minmax(300px,.8fr) minmax(460px,1.2fr); } .mount-grid { grid-template-columns: 1fr; } .mount-card { grid-template-columns: minmax(110px,.8fr) repeat(3,minmax(80px,1fr)); } .ship-quick-stats { grid-template-columns: 1fr; } }
@media (max-width: 920px) { .master-data-metrics { grid-template-columns: repeat(2,minmax(0,1fr)); } .master-data-workspace { grid-template-columns: 1fr; } .catalog-panel { position: static; max-height: none; } .catalog-scroll { max-height: 34rem; } .ship-quick-stats { grid-template-columns: repeat(3,minmax(70px,1fr)); } }
@media (max-width: 640px) { .master-data-tabs { grid-template-columns: 1fr; } .catalog-toolbar, .form-grid.two-columns, .two-columns, .form-grid.three-columns, .choice-grid { grid-template-columns: 1fr; } .catalog-record { grid-template-columns: 1fr; } .record-meta { justify-content: flex-start; padding-left: 3.3rem; } .editor-header-with-preview { align-items: flex-start; flex-wrap: wrap; } .ship-quick-stats { width: 100%; margin-left: 0; } .mount-card { grid-template-columns: 1fr; } .editor-actions { align-items: stretch; flex-direction: column; } .editor-actions .primary-action { width: 100%; } }
</style>
