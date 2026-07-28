import assert from 'node:assert/strict'
import test from 'node:test'

import {
  formatBuildModifier,
  isActiveBuildEffect,
  roundByPrecision,
} from '../src/modules/builds/domain/buildStatPresentation.js'


test('composite modifiers keep percentage and flat units separate', () => {
  assert.equal(formatBuildModifier({
    percent_modifier: 9.2,
    flat_modifier: 4.1,
    precision: 1,
    unit: 'kn',
  }), '+9.2% · +4.1 kn')
})


test('active effects hide duplicate core components and base-speed helper row', () => {
  assert.equal(isActiveBuildEffect({ key: 'speed_min_knots', modifier: 0.7 }), false)
  assert.equal(isActiveBuildEffect({ key: 'speed_bonus_knots', modifier: 4.1 }), false)
  assert.equal(isActiveBuildEffect({ key: 'speed_knots', modifier: 4.8 }), true)
  assert.equal(isActiveBuildEffect({ key: 'damage_pct', modifier: 5 }), true)
})


test('display rounding follows the shared half-up contract for both signs', () => {
  assert.equal(roundByPrecision(1.25, 1), 1.3)
  assert.equal(roundByPrecision(-1.25, 1), -1.3)
})
