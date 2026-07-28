import test from 'node:test'
import assert from 'node:assert/strict'

import { calculateBuildStatRows } from '../src/modules/builds/buildCalculations.js'
import { calculateSpecialistEffectTotals } from '../src/modules/builds/specialistEffects.js'

test('each specialist type contributes once regardless of submitted quantity', () => {
  const totals = calculateSpecialistEffectTotals({
    slots: [{ item: 'First Mate', quantity: 99 }],
    effectForItem: () => ({
      sail_deployment_speed_per_sailor_pct: 0.2,
      repair_speed_per_sailor_pct: 0.3,
      crew_capacity: 3,
    }),
    crew: { sailors: 80 },
  })
  assert.deepEqual(totals, { sail_deployment_speed_pct: 16, repair_speed_pct: 24, crew_capacity: 3 })
})


test('specialist totals use shared half-up rounding for negative ties', () => {
  const totals = calculateSpecialistEffectTotals({
    slots: [{ item: 'Test Specialist' }],
    effectForItem: () => ({ sail_deployment_speed_per_sailor_pct: -0.123445 }),
    crew: { sailors: 10 },
  })
  assert.deepEqual(totals, { sail_deployment_speed_pct: -1.2345 })
})


test('First Mate changes sail deployment but not Zeven ship speed', () => {
  const specialistEffects = calculateSpecialistEffectTotals({
    slots: [{ item: 'First Mate' }],
    effectForItem: () => ({ sail_deployment_speed_per_sailor_pct: 0.2 }),
    crew: { sailors: 102, soldiers: 56, musketeers: 30 },
  })
  const sailEffects = { speed_knots: 4.1 }
  const effects = { ...specialistEffects, ...sailEffects }
  const rows = calculateBuildStatRows({
    ship: { speed_min_knots: 7.7, speed_knots: 10.6 },
    effects,
    effectSets: [sailEffects, specialistEffects],
    definitions: [
      {
        key: 'speed_knots',
        base_field: 'speed_knots',
        pct_effect: 'speed_pct',
        calculation_flat_effect: 'speed_knots',
        pct_base_field: 'speed_min_knots',
        precision: 1,
        positive_is_good: true,
      },
      {
        key: 'sail_deployment_speed_pct',
        base_field: null,
        flat_effect: 'sail_deployment_speed_pct',
        unit: '%',
        precision: 1,
        positive_is_good: true,
      },
    ],
  })
  const byKey = Object.fromEntries(rows.map((row) => [row.key, row]))

  assert.deepEqual(specialistEffects, { sail_deployment_speed_pct: 20.4 })
  assert.equal(byKey.speed_knots.percent_modifier, null)
  assert.equal(byKey.speed_knots.flat_modifier, 4.1)
  assert.equal(byKey.speed_knots.effective, 14.7)
  assert.equal(byKey.sail_deployment_speed_pct.modifier, 20.4)
})
