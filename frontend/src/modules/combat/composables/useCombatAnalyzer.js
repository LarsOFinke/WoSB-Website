import { computed, onMounted, reactive, ref, watch } from 'vue'

import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'
import { useLocale } from '@/locales'
import { getBuildOptions } from '@/modules/builds/api/builds'
import { sortShipsForDropdown } from '@/modules/builds/buildForm'
import { useBuildCatalog } from '@/modules/builds/composables/useBuildCatalog'
import { useBuildInventory } from '@/modules/builds/composables/useBuildInventory'
import { emptyInventorySlot } from '@/modules/builds/inventorySlots'
import { listShips } from '@/modules/ships/api/ships'
import {
  buildCombatEffectSets,
  calculateArcDpm,
  isCombatRelevantOption,
} from '@/modules/combat/domain/combatDpm'

const EMPTY_CATALOG = {
  build_roles: [],
  categories: [],
  options: {},
  stat_definitions: [],
  limits: {},
}
const WEAPON_FIELDS = ['port_weapon_slots', 'front_weapon_slots', 'rear_weapon_slots']

function createForm() {
  return {
    ship_id: '',
    lantern: '',
    upgrades: Array.from({ length: 8 }, () => ''),
    specialists: Array.from({ length: 4 }, () => ''),
    sailors: 0,
    low_durability: false,
    port_weapon_slots: [emptyInventorySlot()],
    starboard_weapon_slots: [emptyInventorySlot()],
    front_weapon_slots: [emptyInventorySlot()],
    rear_weapon_slots: [emptyInventorySlot()],
    mortar_weapon_slots: [emptyInventorySlot()],
    special_weapon_slots: [emptyInventorySlot()],
    mortar_modification_installed: false,
    armor: {
      oneSide: 2.4,
      bothSides: 2.4,
      bow: 2.4,
      stern: 2.4,
    },
  }
}

export function useCombatAnalysisPage() {
  const { optionLabel, t } = useLocale()
  const ships = ref([])
  const optionCatalog = ref({ ...EMPTY_CATALOG })
  const loading = ref(false)
  const error = ref('')
  const form = reactive(createForm())
  const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(form.ship_id)) || null)

  const catalog = useBuildCatalog({
    ships,
    optionCatalog,
    selectedShip,
    optionLabel,
    t,
    slotPlaceholderSrc,
  })
  const inventory = useBuildInventory({
    form,
    optionCatalog,
    selectedShip,
    optionMeta: catalog.optionMeta,
    optionLabel,
  })

  const weaponOptionsByName = computed(() => new Map(
    (optionCatalog.value.options?.weapon || []).map((option) => [option.name, option]),
  ))
  const optionByName = (name) => weaponOptionsByName.value.get(name) || null

  const upgradeOptions = computed(() => (optionCatalog.value.options?.upgrade || [])
    .filter(isCombatRelevantOption)
    .sort((left, right) => optionLabel(left.name).localeCompare(optionLabel(right.name))))
  const specialistOptions = computed(() => (optionCatalog.value.options?.special_crew || [])
    .filter(isCombatRelevantOption)
    .sort((left, right) => optionLabel(left.name).localeCompare(optionLabel(right.name))))
  const lanternOptions = computed(() => (optionCatalog.value.options?.lantern || [])
    .filter(isCombatRelevantOption)
    .sort((left, right) => optionLabel(left.name).localeCompare(optionLabel(right.name))))

  const availableUpgradeSlots = computed(() => Math.min(8, Math.max(0, Number(selectedShip.value?.upgrade_slots) || 0)))
  const selectedUpgradeOptions = computed(() => form.upgrades
    .slice(0, availableUpgradeSlots.value)
    .filter(Boolean)
    .map((name) => (optionCatalog.value.options?.upgrade || []).find((option) => option.name === name))
    .filter(Boolean))
  const selectedSpecialistOptions = computed(() => form.specialists
    .filter(Boolean)
    .map((name) => (optionCatalog.value.options?.special_crew || []).find((option) => option.name === name))
    .filter(Boolean))
  const selectedLantern = computed(() => (optionCatalog.value.options?.lantern || [])
    .find((option) => option.name === form.lantern) || null)

  const effectSets = computed(() => buildCombatEffectSets({
    lantern: selectedLantern.value,
    upgrades: selectedUpgradeOptions.value,
    specialists: selectedSpecialistOptions.value,
    lowDurability: form.low_durability,
    sailors: form.sailors,
  }))

  const results = computed(() => ({
    oneSide: calculateArcDpm({
      slots: form.port_weapon_slots,
      optionByName,
      armor: form.armor.oneSide,
      effectSets: effectSets.value,
    }),
    bothSides: calculateArcDpm({
      slots: form.port_weapon_slots,
      optionByName,
      armor: form.armor.bothSides,
      effectSets: effectSets.value,
      quantityMultiplier: 2,
    }),
    bow: calculateArcDpm({
      slots: form.front_weapon_slots,
      optionByName,
      armor: form.armor.bow,
      effectSets: effectSets.value,
      positional: true,
    }),
    stern: calculateArcDpm({
      slots: form.rear_weapon_slots,
      optionByName,
      armor: form.armor.stern,
      effectSets: effectSets.value,
      positional: true,
    }),
  }))

  function standardWeaponOptionsForField(fieldName, index) {
    return inventory.weaponOptionsForField(fieldName, index).filter((name) => {
      const kind = catalog.optionMeta('weapon', name)?.option_kind
      return fieldName === 'port_weapon_slots' ? kind === 'cannon' : kind === 'bow_stern'
    })
  }

  function upgradePickerOptions(index) {
    const current = form.upgrades[index]
    const selectedElsewhere = new Set(form.upgrades.filter((_, rowIndex) => rowIndex !== index).filter(Boolean))
    return upgradeOptions.value.map((option) => ({
      value: option.name,
      label: optionLabel(option.name),
      meta: catalog.formatEffectMap(option.stat_effects),
      disabled: option.name !== current && selectedElsewhere.has(option.name),
    }))
  }

  function specialistPickerOptions(index) {
    const current = form.specialists[index]
    const selectedElsewhere = new Set(form.specialists.filter((_, rowIndex) => rowIndex !== index).filter(Boolean))
    return specialistOptions.value.map((option) => ({
      value: option.name,
      label: optionLabel(option.name),
      meta: catalog.formatEffectMap(option.stat_effects),
      disabled: option.name !== current && selectedElsewhere.has(option.name),
    }))
  }

  const lanternPickerOptions = computed(() => lanternOptions.value.map((option) => ({
    value: option.name,
    label: optionLabel(option.name),
    meta: catalog.formatEffectMap(option.stat_effects),
  })))

  function resetSelectionsForShip() {
    for (const field of WEAPON_FIELDS) form[field].splice(0, form[field].length, emptyInventorySlot())
    form.starboard_weapon_slots.splice(0, form.starboard_weapon_slots.length, emptyInventorySlot())
    form.upgrades.splice(0, form.upgrades.length, ...Array.from({ length: 8 }, () => ''))
    form.specialists.splice(0, form.specialists.length, ...Array.from({ length: 4 }, () => ''))
    form.lantern = ''
    form.low_durability = false
    form.sailors = Number(selectedShip.value?.sailor_minimum || 0)
  }

  let requestId = 0
  watch(() => form.ship_id, async (shipId, previousShipId) => {
    if (!shipId) return
    const currentRequest = ++requestId
    loading.value = true
    error.value = ''
    try {
      const catalogResponse = await getBuildOptions(Number(shipId))
      if (currentRequest !== requestId) return
      optionCatalog.value = catalogResponse
      if (shipId !== previousShipId) resetSelectionsForShip()
      for (const field of WEAPON_FIELDS) inventory.reconcileInventoryField(field)
    } catch (err) {
      if (currentRequest === requestId) error.value = err.message || t('combatAnalysis.loadError')
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  })

  watch(availableUpgradeSlots, (limit) => {
    for (let index = limit; index < form.upgrades.length; index += 1) form.upgrades[index] = ''
  })

  onMounted(async () => {
    loading.value = true
    error.value = ''
    try {
      ships.value = sortShipsForDropdown(await listShips())
      form.ship_id = ships.value[0]?.id || ''
      if (!form.ship_id) loading.value = false
    } catch (err) {
      error.value = err.message || t('combatAnalysis.loadError')
      loading.value = false
    }
  })

  return {
    t,
    optionLabel,
    form,
    ships,
    loading,
    error,
    selectedShip,
    shipPickerOptions: catalog.shipPickerOptions,
    selectedShipImage: catalog.selectedShipImage,
    availableUpgradeSlots,
    upgradePickerOptions,
    specialistPickerOptions,
    lanternPickerOptions,
    standardWeaponOptionsForField,
    weaponCapacityForField: inventory.weaponCapacityForField,
    slotQuantityTotal: inventory.slotQuantityTotal,
    quantityMaxForField: inventory.quantityMaxForField,
    onInventoryItemChange: inventory.onInventoryItemChange,
    onInventoryQuantityChange: inventory.onInventoryQuantityChange,
    results,
  }
}
