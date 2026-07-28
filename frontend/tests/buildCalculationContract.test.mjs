import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { calculateBuildStatRows } from '../src/modules/builds/buildCalculations.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const contract = JSON.parse(fs.readFileSync(
  path.resolve(here, '../../contracts/build-calculation-cases.json'),
  'utf8',
))

for (const calculationCase of contract.cases) {
  test(`frontend calculation contract: ${calculationCase.id}`, () => {
    const rows = calculateBuildStatRows({
      ship: calculationCase.ship,
      definitions: calculationCase.definitions,
      effects: calculationCase.effects,
      effectSets: calculationCase.effect_sets,
    })
    const byKey = Object.fromEntries(rows.map((row) => [row.key, row]))
    for (const [key, expected] of Object.entries(calculationCase.expected)) {
      for (const [fieldName, expectedValue] of Object.entries(expected)) {
        assert.equal(byKey[key][fieldName], expectedValue, `${key}.${fieldName}`)
      }
    }
  })
}
