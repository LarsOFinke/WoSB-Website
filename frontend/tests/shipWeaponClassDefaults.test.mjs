import test from 'node:test'
import assert from 'node:assert/strict'

import {
  applyRateWeaponClassDefaults,
  rateWeaponClass,
} from '../src/modules/admin/domain/shipWeaponClassDefaults.js'

const rules = [
  { rate: 1, weapon_class: 'heavy' },
  { rate: 2, weapon_class: 'heavy' },
  { rate: 3, weapon_class: 'medium' },
  { rate: 4, weapon_class: 'medium' },
  { rate: 5, weapon_class: 'light' },
  { rate: 6, weapon_class: 'light' },
  { rate: 7, weapon_class: 'light' },
]

test('rate defaults follow the normalized weapon-class taxonomy', () => {
  assert.equal(rateWeaponClass(rules, 7), 'light')
  assert.equal(rateWeaponClass(rules, 5), 'light')
  assert.equal(rateWeaponClass(rules, 4), 'medium')
  assert.equal(rateWeaponClass(rules, 3), 'medium')
  assert.equal(rateWeaponClass(rules, 2), 'heavy')
  assert.equal(rateWeaponClass(rules, 1), 'heavy')
})

test('new ship defaults affect regular mounts but not mortars or special weapons', () => {
  const mounts = [
    { slot_type: 'weapon_front', max_weapon_class: '' },
    { slot_type: 'weapon_rear', max_weapon_class: '' },
    { slot_type: 'weapon_port', max_weapon_class: '' },
    { slot_type: 'weapon_starboard', max_weapon_class: '' },
    { slot_type: 'weapon_mortar', max_weapon_class: '' },
    { slot_type: 'weapon_special', max_weapon_class: '' },
  ]

  applyRateWeaponClassDefaults(mounts, rules, 4, { force: true })

  assert.deepEqual(mounts.map((row) => row.max_weapon_class), [
    'medium', 'medium', 'medium', 'medium', '', '',
  ])
})

test('changing rate updates inherited defaults and preserves explicit exceptions', () => {
  const mounts = [
    { slot_type: 'weapon_front', max_weapon_class: 'light' },
    { slot_type: 'weapon_rear', max_weapon_class: 'heavy' },
  ]

  applyRateWeaponClassDefaults(mounts, rules, 4, { previousRate: 5 })

  assert.equal(mounts[0].max_weapon_class, 'medium')
  assert.equal(mounts[1].max_weapon_class, 'heavy')
})
