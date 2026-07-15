import { computed } from 'vue'

import { slotLimits, weaponArcFields } from '@/modules/builds/buildForm'
import {
  inventoryQuantityTotal,
  isWeaponInventoryField,
  normalizeInventorySlots,
  reconcileInventorySlots,
  remainingInventoryQuantity,
  selectInventoryItem,
  setInventoryQuantity,
} from '@/modules/builds/inventorySlots'

const WEAPON_SLOT_TYPES = {
  front_weapon_slots: 'weapon_front',
  rear_weapon_slots: 'weapon_rear',
  port_weapon_slots: 'weapon_port',
  starboard_weapon_slots: 'weapon_starboard',
  mortar_weapon_slots: 'weapon_mortar',
  special_weapon_slots: 'weapon_special',
}

export function useBuildInventory({ form, optionCatalog, selectedShip, optionMeta, optionLabel }) {
  const weaponSlotTypeForField = (fieldName) => WEAPON_SLOT_TYPES[fieldName]

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
    if (!weaponSlotTypeForField(fieldName)) return slotLimits[fieldName]
    return Math.min(slotLimits[fieldName] || 0, weaponCapacityForField(fieldName))
  }

  const availableWeaponArcs = computed(() => weaponArcFields
    .filter((arc) => weaponCapacityForField(arc.fieldName) > 0))

  const slotCount = (fieldName) => normalizeInventorySlots(form[fieldName]).length
  const slotQuantityTotal = (fieldName) => inventoryQuantityTotal(form[fieldName])
  const allWeaponQuantityTotal = () => weaponArcFields
    .reduce((total, arc) => total + slotQuantityTotal(arc.fieldName), 0)
  const isOptionUsed = (slots, option, currentIndex) => slots
    .some((slot, index) => index !== currentIndex && slot.item === option)

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
    const selectedElsewhere = new Set((form[fieldName] || [])
      .filter((_, index) => index !== currentIndex)
      .map((slot) => slot.item)
      .filter(Boolean))
    return (optionCatalog.value.options?.weapon || [])
      .filter((option) => isWeaponOptionAllowedForField(option, fieldName))
      .map((option) => option.name)
      .filter((option) => option === current || !selectedElsewhere.has(option))
      .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
  }

  const isWeaponFieldUnavailable = (fieldName) => Boolean(weaponSlotTypeForField(fieldName))
    && weaponCapacityForField(fieldName) <= 0
  const weaponFieldOverCapacity = (fieldName) => slotQuantityTotal(fieldName) > weaponCapacityForField(fieldName)

  function weaponSelectionInvalid(fieldName, optionName) {
    if (!optionName || !isWeaponInventoryField(fieldName)) return false
    const option = optionMeta('weapon', optionName)
    return !option || !isWeaponOptionAllowedForField(option, fieldName)
  }

  const allWeaponsValid = computed(() => weaponArcFields.every((arc) => {
    if (weaponFieldOverCapacity(arc.fieldName)) return false
    return normalizeInventorySlots(form[arc.fieldName])
      .every((slot) => !weaponSelectionInvalid(arc.fieldName, slot.item))
  }))

  function quantityCapacityForField(fieldName) {
    return isWeaponInventoryField(fieldName) ? weaponCapacityForField(fieldName) : null
  }

  function quantityMaxForField(fieldName, index) {
    const capacity = quantityCapacityForField(fieldName)
    return capacity === null
      ? 999999
      : Math.max(1, remainingInventoryQuantity(form[fieldName], index, capacity))
  }

  function reconcileOptions(fieldName) {
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
      reconcileInventorySlots(form[fieldName], slotLimitForField(fieldName), reconcileOptions(fieldName)),
    )
  }

  function onInventoryItemChange(fieldName, index, event) {
    replaceInventorySlots(fieldName, selectInventoryItem(
      form[fieldName], index, event.target.value, slotLimitForField(fieldName), reconcileOptions(fieldName),
    ))
  }

  function onInventoryQuantityChange(fieldName, index, event) {
    replaceInventorySlots(fieldName, setInventoryQuantity(
      form[fieldName], index, event.target.value, slotLimitForField(fieldName), reconcileOptions(fieldName),
    ))
  }

  return {
    availableWeaponArcs,
    slotCount,
    slotQuantityTotal,
    allWeaponQuantityTotal,
    isOptionUsed,
    weaponCapacityForField,
    slotLimitForField,
    weaponOptionsForField,
    isWeaponFieldUnavailable,
    weaponFieldOverCapacity,
    weaponSelectionInvalid,
    allWeaponsValid,
    quantityMaxForField,
    reconcileInventoryField,
    onInventoryItemChange,
    onInventoryQuantityChange,
  }
}
