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
    const modification = form.mortar_modification_installed
      ? selectedShip.value.mortar_modification
      : null
    const capacityMap = {
      front_weapon_slots: selectedShip.value.front_weapon_capacity,
      rear_weapon_slots: selectedShip.value.rear_weapon_capacity,
      port_weapon_slots: Number(selectedShip.value.broadside_weapon_capacity || 0)
        + Number(modification?.broadside_capacity_delta || 0),
      starboard_weapon_slots: Number(selectedShip.value.broadside_weapon_capacity || 0)
        + Number(modification?.broadside_capacity_delta || 0),
      mortar_weapon_slots: Number(selectedShip.value.mortar_weapon_capacity || 0)
        + Number(modification?.mortar_capacity || 0),
      special_weapon_slots: selectedShip.value.dedicated_special_weapon_capacity,
    }
    return Math.max(0, Number(capacityMap[fieldName]) || 0)
  }

  function specialWeaponCapacityForField(fieldName) {
    if (!selectedShip.value) return 0
    const capacityMap = {
      front_weapon_slots: selectedShip.value.front_special_weapon_capacity,
      rear_weapon_slots: selectedShip.value.rear_special_weapon_capacity,
      special_weapon_slots: selectedShip.value.dedicated_special_weapon_capacity,
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
      const maxCaliber = Number(form.mortar_modification_installed
        ? selectedShip.value?.mortar_modification?.max_caliber_inches
          ?? selectedShip.value?.max_mortar_caliber_inches
        : selectedShip.value?.max_mortar_caliber_inches)
      const optionCaliber = Number(option.weapon_caliber_inches)
      if (Number.isFinite(maxCaliber) && Number.isFinite(optionCaliber) && optionCaliber > maxCaliber) return false
      return ['mortar', 'mortar_launcher'].includes(option.option_kind)
    }
    if (slotType === 'weapon_special') return option.option_kind === 'special_weapon'
    if (option.option_kind === 'special_weapon') {
      return ['weapon_front', 'weapon_rear'].includes(slotType)
        && specialWeaponCapacityForField(fieldName) > 0
    }
    return !['mortar', 'mortar_launcher'].includes(option.option_kind)
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
  const specialWeaponQuantityTotal = (fieldName, excludedIndex = -1) => (
    Array.isArray(form[fieldName]) ? form[fieldName] : []
  ).reduce((total, slot, index) => {
    if (index === excludedIndex || !String(slot?.item || '').trim()) return total
    const option = optionMeta('weapon', slot.item)
    return total + (
      option?.option_kind === 'special_weapon'
        ? Math.max(1, Number(slot.quantity) || 1)
        : 0
    )
  }, 0)
  const weaponFieldOverCapacity = (fieldName) => (
    slotQuantityTotal(fieldName) > weaponCapacityForField(fieldName)
    || specialWeaponQuantityTotal(fieldName) > specialWeaponCapacityForField(fieldName)
  )

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
    if (capacity === null) return 999999
    const regularRemaining = Math.max(
      1,
      remainingInventoryQuantity(form[fieldName], index, capacity),
    )
    const item = form[fieldName]?.[index]?.item
    const option = item ? optionMeta('weapon', item) : null
    if (option?.option_kind !== 'special_weapon') return regularRemaining
    const specialRemaining = Math.max(
      1,
      specialWeaponCapacityForField(fieldName)
        - specialWeaponQuantityTotal(fieldName, index),
    )
    return Math.min(regularRemaining, specialRemaining)
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
