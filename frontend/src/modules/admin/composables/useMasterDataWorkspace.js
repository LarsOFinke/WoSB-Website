import { computed, onMounted, reactive, ref } from 'vue'

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
import {
  availableUpgradeOptions,
  categoryFormValues,
  categoryPayload,
  createCategoryForm,
  createOptionForm,
  createShipForm,
  optionFormValues,
  optionPayload,
  parseEffectObject,
  shipFormValues,
  shipPayload,
  weaponMountRows,
} from '@/modules/admin/domain/masterDataForms'
import { absoluteFileUrl } from '@/modules/files/api/files'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

const EMPTY_OVERVIEW = {
  category_count: 0,
  option_count: 0,
  ship_count: 0,
  overridden_count: 0,
  inactive_count: 0,
}

export function useMasterDataWorkspace() {
  const { t } = useLocale()
  const activeTab = ref('ships')
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const success = ref('')
  const overview = ref({ ...EMPTY_OVERVIEW })
  const taxonomy = ref({ weapon_classes: [], weapon_slot_types: [] })
  const categories = ref([])
  const options = ref([])
  const upgradeOptions = ref([])
  const ships = ref([])
  const optionCategory = ref('')
  const optionSearch = ref('')
  const shipSearch = ref('')
  const categoryEditingId = ref(null)
  const optionEditingId = ref(null)
  const shipEditingId = ref(null)
  const effectsText = ref('{}')
  const categoryForm = reactive(createCategoryForm())
  const optionForm = reactive(createOptionForm())
  const shipForm = reactive(createShipForm())

  const selectedOption = computed(() => options.value.find((row) => row.id === optionEditingId.value))
  const selectedShip = computed(() => ships.value.find((row) => row.id === shipEditingId.value))
  const tabCounts = computed(() => ({
    options: overview.value.option_count,
    ships: overview.value.ship_count,
    categories: overview.value.category_count,
  }))

  const seedStatusClass = (row) => `status-${row?.seed_status || 'custom'}`
  const seedStatusLabel = (row) => t(`masterData.seedStatus.${row?.seed_status || 'custom'}`)
  const visibleMounts = (mounts = []) => mounts.filter((mount) => Number(mount.capacity || 0) > 0)
  const imagePreview = (url) => absoluteFileUrl(url)
  const mountLabel = (slotType) => taxonomy.value.weapon_slot_types
    .find((row) => row.code === slotType)?.label || slotType

  function clearMessages() {
    error.value = ''
    success.value = ''
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
    return weaponMountRows(taxonomy.value.weapon_slot_types, rows)
  }

  function resetCategory(row = null) {
    categoryEditingId.value = row?.id || null
    Object.assign(categoryForm, categoryFormValues(row))
    clearMessages()
  }

  function resetOption(row = null) {
    optionEditingId.value = row?.id || null
    Object.assign(optionForm, optionFormValues(row, categories.value[0]?.id || ''))
    effectsText.value = JSON.stringify(row?.stat_effects || {}, null, 2)
    clearMessages()
  }

  function resetShip(row = null) {
    shipEditingId.value = row?.id || null
    Object.assign(shipForm, shipFormValues(row, taxonomy.value.weapon_slot_types))
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

  async function runSave(action, reload, reset) {
    clearMessages()
    saving.value = true
    try {
      await action()
      await Promise.all([reload(), loadOverview()])
      reset()
      success.value = t('masterData.saved')
    } catch (err) {
      error.value = err.message || t('masterData.saveError')
    } finally {
      saving.value = false
    }
  }

  function saveCategory() {
    const editingId = categoryEditingId.value
    const payload = categoryPayload(categoryForm, !editingId)
    return runSave(
      () => editingId
        ? updateMasterDataCategory(editingId, payload)
        : createMasterDataCategory(payload),
      loadCategories,
      resetCategory,
    )
  }

  function parseEffects() {
    return parseEffectObject(effectsText.value, t('masterData.effectsError'))
  }

  function saveOption() {
    const editingId = optionEditingId.value
    return runSave(
      () => editingId
        ? updateMasterDataOption(editingId, optionPayload(optionForm, parseEffects()))
        : createMasterDataOption(optionPayload(optionForm, parseEffects())),
      loadOptions,
      resetOption,
    )
  }

  function upgradeOptionById(optionId) {
    return upgradeOptions.value.find((row) => row.id === Number(optionId))
  }

  function upgradeChoicesForOverride(index) {
    return availableUpgradeOptions(upgradeOptions.value, shipForm.upgrade_effect_overrides, index)
  }

  function addUpgradeOverride() {
    const [option] = availableUpgradeOptions(upgradeOptions.value, shipForm.upgrade_effect_overrides, -1)
    if (option) shipForm.upgrade_effect_overrides.push({ option_id: option.id, effects_text: '{}' })
  }

  function removeUpgradeOverride(index) {
    shipForm.upgrade_effect_overrides.splice(index, 1)
  }

  function parseShipUpgradeOverrides() {
    return shipForm.upgrade_effect_overrides.map((row) => ({
      option_id: Number(row.option_id),
      stat_effects: parseEffectObject(row.effects_text, t('masterData.effectsError')),
    }))
  }

  function saveShip() {
    const editingId = shipEditingId.value
    const payload = shipPayload(shipForm, parseShipUpgradeOverrides())
    return runSave(
      () => editingId ? updateMasterDataShip(editingId, payload) : createMasterDataShip(payload),
      loadShips,
      resetShip,
    )
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

  const deactivateCategory = (row) => runRecordAction(
    () => deactivateMasterDataCategory(row.id),
    loadCategories,
    categoryEditingId.value === row.id ? resetCategory : null,
  )
  const deactivateOption = (row) => runRecordAction(
    () => deactivateMasterDataOption(row.id),
    loadOptions,
    optionEditingId.value === row.id ? resetOption : null,
  )
  const deactivateShip = (row) => runRecordAction(
    () => deactivateMasterDataShip(row.id),
    loadShips,
    shipEditingId.value === row.id ? resetShip : null,
  )
  const restoreCategory = (row) => runRecordAction(() => restoreMasterDataCategory(row.id), loadCategories, resetCategory)
  const restoreOption = (row) => runRecordAction(() => restoreMasterDataOption(row.id), loadOptions, resetOption)
  const restoreShip = (row) => runRecordAction(() => restoreMasterDataShip(row.id), loadShips, resetShip)

  useDebouncedWatch([optionCategory, optionSearch], loadOptions, 180)
  useDebouncedWatch(shipSearch, loadShips, 180)
  onMounted(reloadAll)

  return {
    t, activeTab, loading, saving, error, success, overview, taxonomy, categories, options,
    upgradeOptions, ships, optionCategory, optionSearch, shipSearch, categoryEditingId,
    optionEditingId, shipEditingId, effectsText, categoryForm, optionForm, shipForm,
    selectedOption, selectedShip, tabCounts, seedStatusClass, mountLabel, visibleMounts,
    seedStatusLabel, clearMessages, imagePreview, applyUploadedImage, blankMounts,
    resetCategory, resetOption, resetShip, loadOverview, loadCategories, loadOptions,
    loadUpgradeOptions, loadShips, reloadAll, saveCategory, parseEffects, saveOption,
    upgradeOptionById, upgradeChoicesForOverride, addUpgradeOverride, removeUpgradeOverride,
    parseShipUpgradeOverrides, saveShip, deactivateCategory, deactivateOption, deactivateShip,
    restoreCategory, restoreOption, restoreShip,
  }
}
