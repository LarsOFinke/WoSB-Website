import { computed } from 'vue'

import { buildCategoryVisuals, buildCrewVisuals, buildVisualUrl } from '@/modules/builds/buildVisuals'
import { absoluteFileUrl } from '@/modules/files/api/files'

export function useBuildCatalog({ ships, optionCatalog, selectedShip, optionLabel, t, slotPlaceholderSrc }) {
  const buildTypeOptions = computed(() => {
    const roles = optionCatalog.value.build_roles || []
    if (roles.length) return roles.map((role) => ({ value: role.slug, label: role.label, meta: role.description || '' }))
    return [
      { value: 'balanced', label: t('builds.types.balanced') },
      { value: 'gunnery', label: t('builds.types.gunnery') },
      { value: 'boarding', label: t('builds.types.boarding') },
      { value: 'defensive', label: t('builds.types.defensive') },
    ]
  })

  function optionsFor(categoryKey) {
    return (optionCatalog.value.options?.[categoryKey] || [])
      .map((option) => option.name)
      .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
  }

  function optionMeta(categoryKey, name) {
    return (optionCatalog.value.options?.[categoryKey] || []).find((option) => option.name === name)
  }

  function optionEffects(categoryKey, name) {
    return optionMeta(categoryKey, name)?.stat_effects || {}
  }

  function optionImage(categoryKey, name) {
    return absoluteFileUrl(optionMeta(categoryKey, name)?.image_url)
      || buildCategoryVisuals[categoryKey]
      || slotPlaceholderSrc
  }

  const selectedShipImage = computed(() => absoluteFileUrl(selectedShip.value?.image_url) || buildVisualUrl('ship'))
  const shipPickerOptions = computed(() => ships.value.map((ship) => ({
    value: ship.id,
    label: ship.name,
    image: absoluteFileUrl(ship.image_url) || buildVisualUrl('ship'),
    meta: [ship.ship_type, ship.rate ? `${t('common.rate')} ${ship.rate}` : ''].filter(Boolean).join(' · '),
  })))

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

  const upgradeEffects = (name) => optionEffects('upgrade', name)
  const specialCrewEffects = (name) => optionEffects('special_crew', name)

  function statLabel(key) {
    const definition = (optionCatalog.value.stat_definitions || []).find(
      (row) => row.pct_effect === key || row.flat_effect === key || row.key === key,
    )
    const path = `builds.statLabels.${definition?.key || key}`
    const translated = t(path)
    return translated === path ? (definition?.label || String(key).replaceAll('_', ' ')) : translated
  }

  function formatEffectMap(effects) {
    const entries = Object.entries(effects || {})
      .filter(([, value]) => Number(value) !== 0)
    return entries.map(([key, value]) => {
      if (key.endsWith('_enabled')) return statLabel(key)
      const number = Number(value)
      const display = number > 0 ? `+${number}` : String(number)
      return `${statLabel(key)} ${display}${key.endsWith('_pct') ? '%' : ''}`
    }).join(' · ')
  }

  function formatEffects(name, categoryKey = 'upgrade') {
    return formatEffectMap(optionEffects(categoryKey, name))
  }

  return {
    buildCrewVisuals,
    buildTypeOptions,
    optionsFor,
    optionMeta,
    optionEffects,
    optionImage,
    selectedShipImage,
    shipPickerOptions,
    inventoryCategory,
    inventoryImage,
    upgradeEffects,
    specialCrewEffects,
    formatEffectMap,
    formatEffects,
  }
}
