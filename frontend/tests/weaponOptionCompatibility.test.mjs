import assert from 'node:assert/strict'
import test from 'node:test'

import {
  isMortarOptionCompatible,
  isMortarOptionKind,
} from '../src/modules/builds/domain/weaponOptionCompatibility.js'

test('Heavy Mortar remains available regardless of a mortar slot caliber limit', () => {
  const heavyMortar = {
    option_kind: 'mortar_universal',
    weapon_caliber_inches: 11,
  }

  assert.equal(isMortarOptionCompatible(heavyMortar, 6), true)
  assert.equal(isMortarOptionCompatible(heavyMortar, 11), true)
  assert.equal(isMortarOptionKind(heavyMortar.option_kind), true)
})

test('ordinary mortars remain constrained by the slot caliber limit', () => {
  assert.equal(isMortarOptionCompatible({
    option_kind: 'mortar',
    weapon_caliber_inches: 11,
  }, 6), false)
})
