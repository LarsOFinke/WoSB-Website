import test from 'node:test'
import assert from 'node:assert/strict'

import { calculateSpecialistEffectTotals } from '../src/modules/builds/specialistEffects.js'

test('each specialist type contributes once regardless of submitted quantity', () => {
  const totals = calculateSpecialistEffectTotals({
    slots: [{ item: 'First Mate', quantity: 99 }],
    effectForItem: () => ({
      speed_per_sailor_pct: 0.2,
      repair_speed_per_sailor_pct: 0.3,
      crew_capacity: 3,
    }),
    crew: { sailors: 80 },
  })
  assert.deepEqual(totals, { speed_pct: 16, repair_speed_pct: 24, crew_capacity: 3 })
})
