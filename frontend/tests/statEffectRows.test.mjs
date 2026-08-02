import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  addEffectRow,
  availableEffectDefinitions,
  effectObjectToRows,
  effectRowsToObject,
} from '../src/modules/admin/domain/statEffectRows.js'

const definitions = [
  { key: 'speed_pct', value_type: 'number' },
  { key: 'steady_course_enabled', value_type: 'boolean' },
]

const masterDataPage = await readFile(new URL('../src/modules/admin/pages/MasterDataPage.vue', import.meta.url), 'utf8')
const statEditor = await readFile(new URL('../src/modules/admin/components/StatEffectEditor.vue', import.meta.url), 'utf8')

test('stat-effect rows preserve the API dictionary without exposing JSON editing', () => {
  const rows = effectObjectToRows({ speed_pct: 5, steady_course_enabled: 1 })
  assert.deepEqual(effectRowsToObject(rows), { speed_pct: 5, steady_course_enabled: 1 })
})

test('stat-effect choices prevent duplicate stats and initialize typed values', () => {
  const rows = [{ key: 'speed_pct', value: 5 }]
  assert.deepEqual(availableEffectDefinitions(definitions, rows, -1), [definitions[1]])
  assert.deepEqual(addEffectRow(rows, definitions), [
    rows[0],
    { key: 'steady_course_enabled', value: 1 },
  ])
})

test('master-data editors use named stat controls instead of JSON dictionaries', () => {
  assert.ok(masterDataPage.includes('<StatEffectEditor'))
  assert.ok(!masterDataPage.includes('effects_text'))
  assert.ok(!masterDataPage.includes('JSON.stringify'))
  assert.ok(statEditor.includes('masterData.effectEditor.stat'))
  assert.ok(statEditor.includes('type="checkbox"'))
})
