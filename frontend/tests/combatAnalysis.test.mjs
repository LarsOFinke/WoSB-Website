import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  buildCombatEffectSets,
  calculateArcDpm,
  combatModifiers,
} from '../src/modules/combat/domain/combatDpm.js'
import { optionPayload } from '../src/modules/admin/domain/masterDataForms.js'

const options = new Map([
  ['6-pdr Rusty Cannon', {
    name: '6-pdr Rusty Cannon',
    weapon_performance: { base_damage: 13, reload_seconds: 10.5 },
  }],
  ['Zeus', { name: 'Zeus', weapon_performance: null }],
])
const optionByName = (name) => options.get(name) || null

test('cannon comparison values reproduce armor-adjusted sustained DPM', () => {
  const result = calculateArcDpm({
    slots: [{ item: '6-pdr Rusty Cannon', quantity: 1 }],
    optionByName,
    armor: 2.4,
  })

  assert.equal(result.armorDpm, 60.6)
  assert.equal(result.rawDpm, 74.3)
  assert.equal(result.rows[0].damageAfterArmor, 10.6)
  assert.equal(result.rows[0].effectiveReload, 10.5)
})

test('side switching doubles the same configured broadside', () => {
  const oneSide = calculateArcDpm({
    slots: [{ item: '6-pdr Rusty Cannon', quantity: 4 }],
    optionByName,
    armor: 8,
  })
  const bothSides = calculateArcDpm({
    slots: [{ item: '6-pdr Rusty Cannon', quantity: 4 }],
    optionByName,
    armor: 8,
    quantityMultiplier: 2,
  })

  assert.equal(bothSides.armorDpm, oneSide.armorDpm * 2)
  assert.equal(bothSides.rows[0].quantity, 8)
})

test('damage, reload and bow/stern modifiers use catalog effect sets', () => {
  const effectSets = buildCombatEffectSets({
    upgrades: [
      { stat_effects: { damage_pct: 10, reload_pct: 20 } },
      { stat_effects: { bow_stern_weapon_damage_pct: 50 } },
    ],
  })

  assert.deepEqual(combatModifiers(effectSets), {
    damageMultiplier: 1.1,
    reloadSpeedMultiplier: 1.2,
    damagePercent: 10.000000000000009,
    reloadPercent: 19.999999999999996,
  })
  const positional = combatModifiers(effectSets, { positional: true })
  assert.equal(positional.damageMultiplier, 1.6500000000000001)
})

test('unverified weapons are reported instead of receiving invented values', () => {
  const result = calculateArcDpm({
    slots: [{ item: 'Zeus', quantity: 2 }],
    optionByName,
    armor: 2.4,
    positional: true,
  })

  assert.equal(result.complete, false)
  assert.equal(result.armorDpm, 0)
  assert.deepEqual(result.missingProfiles, ['Zeus'])
})

test('master-data payload only persists weapon profiles for standard cannon families', () => {
  const base = {
    category_id: 1,
    name: 'Test item',
    source: '',
    notes: '',
    image_url: '',
    weapon_class: '',
    weapon_caliber_inches: '',
    weapon_base_damage: 15,
    weapon_reload_seconds: 10,
    allowed_slot_types: [],
    sort_order: 100,
    is_active: true,
  }
  assert.deepEqual(optionPayload({ ...base, option_kind: 'cannon' }, {}).weapon_performance, {
    base_damage: 15,
    reload_seconds: 10,
  })
  assert.equal(optionPayload({ ...base, option_kind: 'mortar' }, {}).weapon_performance, null)
})

test('combat page exposes four independent armor inputs without per-keystroke API calls', async () => {
  const [page, composable] = await Promise.all([
    readFile(new URL('../src/modules/combat/pages/CombatAnalysisPage.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/combat/composables/useCombatAnalyzer.js', import.meta.url), 'utf8'),
  ])

  for (const key of ['oneSide', 'bothSides', 'bow', 'stern']) {
    assert.match(page, new RegExp(`form\\.armor\\.${key}`))
  }
  assert.match(composable, /watch\(\(\) => form\.ship_id/)
  assert.doesNotMatch(composable, /watch\([^)]*form\.armor/)
  assert.match(composable, /quantityMultiplier: 2/)
})
