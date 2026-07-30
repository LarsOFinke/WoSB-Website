export function createCategoryForm() {
  return { key: '', label: '', sort_order: 100, is_active: true }
}

export function createOptionForm() {
  return {
    category_id: '',
    name: '',
    source: '',
    notes: '',
    image_url: '',
    option_kind: '',
    weapon_class: '',
    weapon_caliber_inches: '',
    weapon_base_damage: '',
    weapon_reload_seconds: '',
    allowed_slot_types: [],
    sort_order: 100,
    is_active: true,
  }
}

export function createShipForm() {
  return {
    name: '',
    rate: 7,
    ship_type: 'Ship',
    durability: 0,
    speed_min_knots: 0,
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
    mortar_modification: null,
    upgrade_effect_overrides: [],
  }
}

export function weaponMountRows(slotTypes, rows = []) {
  const current = new Map(rows.map((row) => [row.slot_type, row]))
  return slotTypes.map((slot) => ({
    slot_type: slot.code,
    capacity: Number(current.get(slot.code)?.capacity || 0),
    special_weapon_capacity: Number(current.get(slot.code)?.special_weapon_capacity || 0),
    max_weapon_class: current.get(slot.code)?.max_weapon_class || '',
    max_caliber_inches: current.get(slot.code)?.max_caliber_inches ?? '',
  }))
}

export function categoryFormValues(row = null) {
  return {
    key: row?.key || '',
    label: row?.label || '',
    sort_order: row?.sort_order ?? 100,
    is_active: row?.is_active ?? true,
  }
}

export function optionFormValues(row = null, fallbackCategoryId = '') {
  return {
    category_id: row?.category_id || fallbackCategoryId,
    name: row?.name || '',
    source: row?.source || '',
    notes: row?.notes || '',
    image_url: row?.image_url || '',
    option_kind: row?.option_kind || '',
    weapon_class: row?.weapon_class || '',
    weapon_caliber_inches: row?.weapon_caliber_inches ?? '',
    weapon_base_damage: row?.weapon_performance?.base_damage ?? '',
    weapon_reload_seconds: row?.weapon_performance?.reload_seconds ?? '',
    allowed_slot_types: [...(row?.allowed_slot_types || [])],
    sort_order: row?.sort_order ?? 100,
    is_active: row?.is_active ?? true,
  }
}

export function shipFormValues(row = null, slotTypes = []) {
  return {
    ...createShipForm(),
    name: row?.name || '',
    rate: row?.rate ?? 7,
    ship_type: row?.ship_type || 'Ship',
    durability: row?.durability ?? 0,
    speed_min_knots: row?.speed_min_knots ?? row?.speed_knots ?? 0,
    speed_knots: row?.speed_knots ?? 0,
    maneuverability: row?.maneuverability ?? 0,
    armor: row?.armor ?? 0,
    hold_capacity: row?.hold_capacity ?? 0,
    crew_capacity: row?.crew_capacity ?? 100,
    sailor_minimum: row?.sailor_minimum ?? 0,
    displacement_tons: row?.displacement_tons ?? 0,
    source: row?.source || '',
    image_url: row?.image_url || '',
    sail_slots: row?.sail_slots ?? 1,
    upgrade_slots: row?.upgrade_slots ?? 5,
    has_lantern: row?.has_lantern ?? true,
    is_active: row?.is_active ?? true,
    weapon_mounts: weaponMountRows(slotTypes, row?.weapon_mounts || []),
    mortar_modification: row?.mortar_modification
      ? { ...row.mortar_modification }
      : null,
    upgrade_effect_overrides: (row?.upgrade_effect_overrides || []).map((override) => ({
      option_id: override.option_id,
      effects_text: JSON.stringify(override.stat_effects || {}, null, 2),
    })),
  }
}

export function parseEffectObject(text, errorMessage) {
  const parsed = JSON.parse(text || '{}')
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(errorMessage)
  return parsed
}

export function categoryPayload(form, includeKey = false) {
  const payload = {
    label: form.label,
    sort_order: Number(form.sort_order),
    is_active: form.is_active,
  }
  return includeKey ? { ...payload, key: form.key } : payload
}

export function optionPayload(form, statEffects) {
  return {
    category_id: Number(form.category_id),
    name: form.name,
    source: form.source || null,
    notes: form.notes || null,
    image_url: form.image_url || null,
    option_kind: form.option_kind || null,
    weapon_class: ['cannon', 'bow_stern'].includes(form.option_kind) ? (form.weapon_class || null) : null,
    weapon_caliber_inches: form.weapon_caliber_inches === '' ? null : Number(form.weapon_caliber_inches),
    weapon_performance: (!['cannon', 'bow_stern'].includes(form.option_kind)
      || form.weapon_base_damage === ''
      || form.weapon_reload_seconds === '')
      ? null
      : {
          base_damage: Number(form.weapon_base_damage),
          reload_seconds: Number(form.weapon_reload_seconds),
        },
    stat_effects: statEffects,
    allowed_slot_types: [...form.allowed_slot_types],
    sort_order: Number(form.sort_order),
    is_active: form.is_active,
  }
}

export function shipPayload(form, upgradeOverrides) {
  return {
    ...form,
    rate: Number(form.rate),
    durability: Number(form.durability),
    speed_min_knots: Number(form.speed_min_knots),
    speed_knots: Number(form.speed_knots),
    maneuverability: Number(form.maneuverability),
    armor: Number(form.armor),
    hold_capacity: Number(form.hold_capacity),
    crew_capacity: Number(form.crew_capacity),
    sailor_minimum: Number(form.sailor_minimum),
    displacement_tons: Number(form.displacement_tons),
    sail_slots: Number(form.sail_slots),
    upgrade_slots: Number(form.upgrade_slots),
    source: form.source || null,
    image_url: form.image_url || null,
    upgrade_effect_overrides: upgradeOverrides,
    weapon_mounts: form.weapon_mounts.map((mount) => ({
      slot_type: mount.slot_type,
      capacity: Number(mount.capacity || 0),
      special_weapon_capacity: Number(mount.special_weapon_capacity || 0),
      max_weapon_class: mount.max_weapon_class || null,
      max_caliber_inches: mount.max_caliber_inches === '' ? null : Number(mount.max_caliber_inches),
    })),
    mortar_modification: form.mortar_modification
      ? {
          ...form.mortar_modification,
          mortar_capacity: Number(form.mortar_modification.mortar_capacity),
          max_caliber_inches: Number(form.mortar_modification.max_caliber_inches),
          broadside_capacity_delta: Number(form.mortar_modification.broadside_capacity_delta),
          durability_delta: Number(form.mortar_modification.durability_delta),
          speed_pct: Number(form.mortar_modification.speed_pct),
          maneuverability_delta: Number(form.mortar_modification.maneuverability_delta),
          hold_capacity_pct: Number(form.mortar_modification.hold_capacity_pct),
          crew_capacity_delta: Number(form.mortar_modification.crew_capacity_delta),
        }
      : null,
  }
}

export function availableUpgradeOptions(options, overrides, index) {
  const current = Number(overrides[index]?.option_id || 0)
  const selected = new Set(overrides.map((row) => Number(row.option_id)).filter(Boolean))
  return options.filter((row) => row.id === current || !selected.has(row.id))
}
