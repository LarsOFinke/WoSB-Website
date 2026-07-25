const PER_CREW_EFFECTS = {
  speed_per_sailor_pct: ['speed_pct', 'sailors'],
  item_reload_per_sailor_pct: ['item_reload_pct', 'sailors'],
  ammo_switch_per_sailor_pct: ['ammo_switch_speed_pct', 'sailors'],
  low_durability_reload_per_sailor_pct: ['low_durability_reload_pct', 'sailors'],
  boarding_cargo_weight_per_boarder_pct: ['boarding_cargo_weight_pct', 'boarders'],
  fishing_catch_per_boarder_pct: ['fishing_catch_pct', 'boarders'],
  fishing_speed_per_sailor_pct: ['fishing_speed_pct', 'sailors'],
  repair_speed_per_sailor_pct: ['repair_speed_pct', 'sailors'],
}

function nonNegativeInteger(value) {
  const number = Number(value)
  return Number.isFinite(number) ? Math.max(0, Math.floor(number)) : 0
}

function addEffect(totals, key, value) {
  totals[key] = (Number(totals[key]) || 0) + Number(value || 0)
}

export function calculateSpecialistEffectTotals({ slots = [], effectForItem, crew = {} }) {
  const counts = {
    sailors: nonNegativeInteger(crew.sailors),
    soldiers: nonNegativeInteger(crew.soldiers),
    musketeers: nonNegativeInteger(crew.musketeers),
    mercenaries: nonNegativeInteger(crew.mercenaries),
  }
  counts.boarders = counts.soldiers + counts.musketeers + counts.mercenaries

  const totals = {}
  for (const slot of slots || []) {
    if (!slot?.item) continue
    const quantity = 1
    const effects = effectForItem?.(slot.item) || {}

    for (const [key, rawValue] of Object.entries(effects)) {
      const value = Number(rawValue || 0)
      if (!Number.isFinite(value) || value === 0) continue

      const dynamic = PER_CREW_EFFECTS[key]
      if (dynamic) {
        const [targetKey, countKey] = dynamic
        addEffect(totals, targetKey, value * counts[countKey] * quantity)
      } else if (key.endsWith('_enabled')) {
        totals[key] = 1
      } else {
        addEffect(totals, key, value * quantity)
      }
    }
  }

  return Object.fromEntries(Object.entries(totals).map(([key, value]) => {
    const rounded = Math.round(Number(value) * 10000) / 10000
    return [key, Number.isInteger(rounded) ? Math.trunc(rounded) : rounded]
  }))
}

export function calculateSpecialistEffectSets({ slots = [], effectForItem, crew = {} }) {
  return (slots || [])
    .filter((slot) => slot?.item)
    .map((slot) => calculateSpecialistEffectTotals({
      slots: [slot],
      effectForItem,
      crew,
    }))
    .filter((effects) => Object.keys(effects).length > 0)
}
