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

const activeTab = ref('options')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const overview = ref({ category_count: 0, option_count: 0, ship_count: 0, overridden_count: 0, inactive_count: 0 })
const taxonomy = ref({ weapon_classes: [], weapon_slot_types: [] })
const categories = ref([])
const options = ref([])
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
})

const selectedOption = computed(() => options.value.find((row) => row.id === optionEditingId.value))
const selectedShip = computed(() => ships.value.find((row) => row.id === shipEditingId.value))

function seedStatusLabel(row) {
  return t(`masterData.seedStatus.${row.seed_status || 'custom'}`)
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
    await Promise.all([loadOptions(), loadShips()])
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

      <section class="master-data-metrics">
        <MetricCard :label="t('masterData.metrics.categories')" :value="overview.category_count" />
        <MetricCard :label="t('masterData.metrics.options')" :value="overview.option_count" />
        <MetricCard :label="t('masterData.metrics.ships')" :value="overview.ship_count" />
        <MetricCard :label="t('masterData.metrics.overrides')" :value="overview.overridden_count" tone="warning" />
        <MetricCard :label="t('masterData.metrics.inactive')" :value="overview.inactive_count" />
      </section>

      <section class="wire-section master-data-tabs">
        <button type="button" :class="{ 'is-active': activeTab === 'options' }" @click="activeTab = 'options'">{{ t('masterData.tabs.options') }}</button>
        <button type="button" :class="{ 'is-active': activeTab === 'ships' }" @click="activeTab = 'ships'">{{ t('masterData.tabs.ships') }}</button>
        <button type="button" :class="{ 'is-active': activeTab === 'categories' }" @click="activeTab = 'categories'">{{ t('masterData.tabs.categories') }}</button>
      </section>

      <p v-if="loading" class="wire-section table-state muted">{{ t('masterData.loading') }}</p>
      <p v-if="error" class="wire-section error-text">{{ error }}</p>
      <p v-if="success" class="wire-section success-text">{{ success }}</p>

      <section v-if="activeTab === 'categories'" class="master-data-workspace">
        <div class="wire-section master-data-list-panel">
          <div class="master-data-panel-heading"><h2>{{ t('masterData.categories.title') }}</h2><button class="small-action" type="button" @click="resetCategory()">{{ t('masterData.new') }}</button></div>
          <article v-for="row in categories" :key="row.id" class="master-data-row" :class="{ 'is-selected': categoryEditingId === row.id }">
            <button class="master-data-row-main" type="button" @click="resetCategory(row)">
              <strong>{{ row.label }}</strong><span>{{ row.key }}</span>
            </button>
            <span class="summary-pill">{{ seedStatusLabel(row) }}</span>
            <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreCategory(row)">{{ t('masterData.restore') }}</button>
            <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateCategory(row)">{{ t('masterData.deactivate') }}</button>
          </article>
        </div>
        <form class="wire-section master-data-editor" @submit.prevent="saveCategory">
          <h2>{{ categoryEditingId ? t('masterData.categories.edit') : t('masterData.categories.create') }}</h2>
          <label><span>{{ t('masterData.fields.key') }}</span><input v-model="categoryForm.key" required maxlength="40" :disabled="Boolean(categoryEditingId)" /></label>
          <label><span>{{ t('masterData.fields.label') }}</span><input v-model="categoryForm.label" required maxlength="80" /></label>
          <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="categoryForm.sort_order" type="number" min="0" /></label>
          <label class="checkbox-line"><input v-model="categoryForm.is_active" type="checkbox" />{{ t('masterData.fields.active') }}</label>
          <button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button>
        </form>
      </section>

      <section v-if="activeTab === 'options'" class="master-data-workspace">
        <div class="wire-section master-data-list-panel">
          <div class="master-data-panel-heading"><h2>{{ t('masterData.options.title') }}</h2><button class="small-action" type="button" @click="resetOption()">{{ t('masterData.new') }}</button></div>
          <div class="master-data-filter-row">
            <select v-model="optionCategory"><option value="">{{ t('masterData.allCategories') }}</option><option v-for="row in categories" :key="row.id" :value="row.key">{{ row.label }}</option></select>
            <input v-model="optionSearch" type="search" :placeholder="t('common.search')" />
          </div>
          <article v-for="row in options" :key="row.id" class="master-data-row" :class="{ 'is-selected': optionEditingId === row.id }">
            <button class="master-data-row-main" type="button" @click="resetOption(row)">
              <strong>{{ row.name }}</strong><span>{{ row.category_label }} · {{ row.option_kind || '—' }}</span>
            </button>
            <span class="summary-pill">{{ seedStatusLabel(row) }}</span>
            <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreOption(row)">{{ t('masterData.restore') }}</button>
            <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateOption(row)">{{ t('masterData.deactivate') }}</button>
          </article>
        </div>

        <form class="wire-section master-data-editor" @submit.prevent="saveOption">
          <h2>{{ optionEditingId ? t('masterData.options.edit') : t('masterData.options.create') }}</h2>
          <div v-if="selectedOption" class="seed-note"><strong>{{ seedStatusLabel(selectedOption) }}</strong><span>{{ selectedOption.seed_status === 'custom' ? t('masterData.customRecord') : selectedOption.seed_revision }}</span></div>
          <label><span>{{ t('masterData.fields.category') }}</span><select v-model="optionForm.category_id" required><option v-for="row in categories" :key="row.id" :value="row.id">{{ row.label }}</option></select></label>
          <label><span>{{ t('masterData.fields.name') }}</span><input v-model="optionForm.name" required maxlength="160" /></label>
          <div class="two-column-fields">
            <label><span>{{ t('masterData.fields.kind') }}</span><input v-model="optionForm.option_kind" maxlength="40" /></label>
            <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="optionForm.sort_order" type="number" min="0" /></label>
          </div>
          <label><span>{{ t('masterData.fields.source') }}</span><input v-model="optionForm.source" maxlength="240" /></label>
          <label><span>{{ t('masterData.fields.notes') }}</span><textarea v-model="optionForm.notes" rows="3" maxlength="500"></textarea></label>
          <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="optionForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
          <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(optionForm, $event)" />
          <img v-if="optionForm.image_url" class="master-data-image-preview" :src="imagePreview(optionForm.image_url)" alt="" />
          <div class="two-column-fields">
            <label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="optionForm.weapon_class"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label>
            <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="optionForm.weapon_caliber_inches" type="number" min="0" step="0.1" /></label>
          </div>
          <fieldset><legend>{{ t('masterData.fields.allowedSlots') }}</legend><label v-for="row in taxonomy.weapon_slot_types" :key="row.code" class="checkbox-line"><input v-model="optionForm.allowed_slot_types" type="checkbox" :value="row.code" />{{ row.label }}</label></fieldset>
          <label><span>{{ t('masterData.fields.effects') }}</span><textarea v-model="effectsText" rows="8" spellcheck="false"></textarea><small>{{ t('masterData.effectsHint') }}</small></label>
          <label class="checkbox-line"><input v-model="optionForm.is_active" type="checkbox" />{{ t('masterData.fields.active') }}</label>
          <button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button>
        </form>
      </section>

      <section v-if="activeTab === 'ships'" class="master-data-workspace">
        <div class="wire-section master-data-list-panel">
          <div class="master-data-panel-heading"><h2>{{ t('masterData.ships.title') }}</h2><button class="small-action" type="button" @click="resetShip()">{{ t('masterData.new') }}</button></div>
          <input v-model="shipSearch" class="master-data-search" type="search" :placeholder="t('common.search')" />
          <article v-for="row in ships" :key="row.id" class="master-data-row" :class="{ 'is-selected': shipEditingId === row.id }">
            <button class="master-data-row-main" type="button" @click="resetShip(row)">
              <strong>{{ row.name }}</strong><span>{{ t('common.rate') }} {{ row.rate }} · {{ row.ship_type }} · {{ row.weapon_layout }}</span>
            </button>
            <span class="summary-pill">{{ seedStatusLabel(row) }}</span>
            <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreShip(row)">{{ t('masterData.restore') }}</button>
            <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateShip(row)">{{ t('masterData.deactivate') }}</button>
          </article>
        </div>

        <form class="wire-section master-data-editor ship-editor" @submit.prevent="saveShip">
          <h2>{{ shipEditingId ? t('masterData.ships.edit') : t('masterData.ships.create') }}</h2>
          <div v-if="selectedShip" class="seed-note"><strong>{{ seedStatusLabel(selectedShip) }}</strong><span>{{ selectedShip.seed_status === 'custom' ? t('masterData.customRecord') : selectedShip.seed_revision }}</span></div>
          <div class="two-column-fields"><label><span>{{ t('masterData.fields.name') }}</span><input v-model="shipForm.name" required maxlength="120" /></label><label><span>{{ t('masterData.fields.type') }}</span><input v-model="shipForm.ship_type" required maxlength="80" /></label></div>
          <div class="three-column-fields"><label><span>{{ t('common.rate') }}</span><input v-model.number="shipForm.rate" type="number" min="1" max="7" /></label><label><span>{{ t('masterData.fields.sailSlots') }}</span><input v-model.number="shipForm.sail_slots" type="number" min="0" /></label><label><span>{{ t('masterData.fields.upgradeSlots') }}</span><input v-model.number="shipForm.upgrade_slots" type="number" min="0" /></label></div>
          <div class="three-column-fields"><label><span>{{ t('masterData.fields.durability') }}</span><input v-model.number="shipForm.durability" type="number" min="0" /></label><label><span>{{ t('masterData.fields.speed') }}</span><input v-model.number="shipForm.speed_knots" type="number" min="0" step="0.1" /></label><label><span>{{ t('masterData.fields.maneuverability') }}</span><input v-model.number="shipForm.maneuverability" type="number" min="0" step="0.1" /></label></div>
          <div class="three-column-fields"><label><span>{{ t('masterData.fields.armor') }}</span><input v-model.number="shipForm.armor" type="number" min="0" step="0.1" /></label><label><span>{{ t('masterData.fields.holdCapacity') }}</span><input v-model.number="shipForm.hold_capacity" type="number" min="0" /></label><label><span>{{ t('masterData.fields.displacement') }}</span><input v-model.number="shipForm.displacement_tons" type="number" min="0" /></label></div>
          <div class="two-column-fields"><label><span>{{ t('masterData.fields.crewCapacity') }}</span><input v-model.number="shipForm.crew_capacity" type="number" min="0" /></label><label><span>{{ t('masterData.fields.sailorMinimum') }}</span><input v-model.number="shipForm.sailor_minimum" type="number" min="0" /></label></div>
          <label><span>{{ t('masterData.fields.source') }}</span><input v-model="shipForm.source" maxlength="240" /></label>
          <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="shipForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
          <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(shipForm, $event)" />
          <img v-if="shipForm.image_url" class="master-data-image-preview ship-preview" :src="imagePreview(shipForm.image_url)" alt="" />
          <fieldset class="mount-grid"><legend>{{ t('masterData.fields.weaponMounts') }}</legend><div v-for="mount in shipForm.weapon_mounts" :key="mount.slot_type" class="mount-row"><strong>{{ taxonomy.weapon_slot_types.find((row) => row.code === mount.slot_type)?.label || mount.slot_type }}</strong><label><span>{{ t('masterData.fields.capacity') }}</span><input v-model.number="mount.capacity" type="number" min="0" /></label><label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="mount.max_weapon_class"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label><label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="mount.max_caliber_inches" type="number" min="0" step="0.1" /></label></div></fieldset>
          <div class="checkbox-grid"><label class="checkbox-line"><input v-model="shipForm.has_lantern" type="checkbox" />{{ t('masterData.fields.lantern') }}</label><label class="checkbox-line"><input v-model="shipForm.is_active" type="checkbox" />{{ t('masterData.fields.active') }}</label></div>
          <button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.master-data-frame { display: grid; gap: 18px; }
.master-data-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.master-data-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.master-data-tabs button { border: 1px solid var(--line-color, #355); background: transparent; color: inherit; padding: 10px 16px; cursor: pointer; }
.master-data-tabs button.is-active { background: rgba(112, 168, 150, 0.18); }
.master-data-workspace { display: grid; grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1.1fr); gap: 18px; align-items: start; }
.master-data-list-panel, .master-data-editor { display: grid; gap: 12px; }
.master-data-panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.master-data-panel-heading h2, .master-data-editor h2 { margin: 0; }
.master-data-filter-row { display: grid; grid-template-columns: 0.8fr 1.2fr; gap: 8px; }
.master-data-search { width: 100%; }
.master-data-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: center; padding: 10px 0; border-top: 1px solid rgba(255,255,255,0.08); }
.master-data-row.is-selected { background: rgba(112, 168, 150, 0.08); }
.master-data-row-main { display: grid; gap: 3px; text-align: left; border: 0; background: transparent; color: inherit; cursor: pointer; min-width: 0; }
.master-data-row-main span { opacity: 0.72; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.master-data-editor label { display: grid; gap: 5px; }
.master-data-editor label > span, .master-data-editor legend { font-size: 0.82rem; opacity: 0.78; }
.master-data-editor input, .master-data-editor select, .master-data-editor textarea, .master-data-filter-row input, .master-data-filter-row select, .master-data-search { width: 100%; box-sizing: border-box; padding: 10px; border: 1px solid rgba(255,255,255,0.16); background: rgba(0,0,0,0.18); color: inherit; }
.two-column-fields, .three-column-fields { display: grid; gap: 10px; }
.two-column-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.three-column-fields { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.checkbox-line { display: flex !important; align-items: center; gap: 8px; }
.checkbox-line input { width: auto; }
.checkbox-grid { display: flex; gap: 20px; flex-wrap: wrap; }
.seed-note { display: flex; justify-content: space-between; gap: 10px; padding: 10px; border: 1px solid rgba(255,255,255,0.12); }
.master-data-image-preview { max-width: 100%; max-height: 180px; object-fit: contain; border: 1px solid rgba(255,255,255,0.12); }
.ship-preview { max-height: 260px; }
.mount-grid { display: grid; gap: 10px; }
.mount-row { display: grid; grid-template-columns: minmax(140px, 1fr) repeat(3, minmax(100px, 0.7fr)); gap: 8px; align-items: end; padding: 10px 0; border-top: 1px solid rgba(255,255,255,0.08); }
@media (max-width: 980px) {
  .master-data-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .master-data-workspace { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .two-column-fields, .three-column-fields, .mount-row, .master-data-filter-row { grid-template-columns: 1fr; }
  .master-data-row { grid-template-columns: 1fr; }
}
</style>
