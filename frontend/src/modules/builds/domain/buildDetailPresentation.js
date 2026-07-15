export function weaponArcRows(build, t) {
  return [
    ['front', 'front_weapon_slots'],
    ['rear', 'rear_weapon_slots'],
    ['port', 'port_weapon_slots'],
    ['starboard', 'starboard_weapon_slots'],
    ['mortar', 'mortar_weapon_slots'],
    ['special', 'special_weapon_slots'],
  ].map(([key, fieldName]) => ({
    key,
    fieldName,
    label: t(`builds.detail.weapons.${key}`),
    slots: build?.[fieldName] || [],
  }))
}

export function buildUpgrades(build) {
  return Array.from({ length: 8 }, (_, offset) => build?.[`upgrade_${offset + 1}`]).filter(Boolean)
}

export function commandDeckSlots(build, optionLabel) {
  return Array.from({ length: 8 }, (_, offset) => {
    const index = offset + 1
    const name = build?.[`upgrade_${index}`] || ''
    return {
      index,
      name,
      label: name ? optionLabel(name) : '',
      effects: '',
      locked: index > Number(build?.ship_stats?.upgrade_slots_available || 0),
    }
  })
}

export function crewDistribution(build, t, crewImages, placeholder) {
  return ['sailors', 'musketeers', 'soldiers', 'mercenaries'].map((key) => ({
    key,
    label: t(`builds.create.crew.${key}`),
    count: build?.[key] || 0,
    image: crewImages[key] || placeholder,
  }))
}

export function inventoryCategory(fieldName) {
  if (fieldName.includes('weapon')) return 'weapon'
  if (fieldName === 'special_crew_slots') return 'special_crew'
  if (fieldName === 'ammunition_slots') return 'ammunition'
  if (fieldName === 'consumable_slots') return 'consumable'
  if (fieldName === 'hold_slots') return 'hold'
  return ''
}

export function slotItem(slot) {
  return typeof slot === 'string' ? slot : (slot?.item || '')
}

export function slotLabel(slot, optionLabel) {
  if (typeof slot === 'string') return optionLabel(slot)
  if (!slot?.item) return ''
  return `${optionLabel(slot.item)} ×${slot.quantity || 1}`
}

export function slotQuantity(slot) {
  if (typeof slot === 'string') return null
  return Number(slot?.quantity || 0) > 1 ? Number(slot.quantity) : null
}

export function specialistLabel(slot, optionLabel) {
  return optionLabel(slotItem(slot))
}

export function shareLinkMeta(slot) {
  return typeof slot === 'string' ? '' : (slot?.notes || '')
}

export function roundByPrecision(value, precision = 0) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const factor = 10 ** Number(precision || 0)
  const rounded = Math.round(Number(value) * factor) / factor
  return Number(precision || 0) === 0 ? Math.round(rounded) : rounded
}

export function formatBuildModifier(row) {
  const value = Number(row.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const sign = value > 0 ? '+' : ''
  const suffix = row.modifier_kind === 'percent'
    || row.unit === '%'
    || String(row.effect_key || '').endsWith('_pct')
    ? '%'
    : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

export function translatedStatRows(build, t) {
  return (build?.ship_stats?.stat_rows || []).map((row) => {
    const path = `builds.statLabels.${row.key}`
    const translated = t(path)
    return {
      ...row,
      label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated,
    }
  })
}

export function activeBuildEffects(statRows) {
  return statRows
    .filter((row) => Number(row.modifier || 0) !== 0)
    .map((row) => ({ ...row, value: formatBuildModifier(row), isDebuff: row.is_debuff }))
}
