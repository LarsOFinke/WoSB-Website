import assert from 'node:assert/strict'
import test from 'node:test'

import { optionPayload } from '../src/modules/admin/domain/masterDataForms.js'

const baseForm = {
  category_id: 1,
  name: 'Test weapon',
  source: '',
  notes: '',
  image_url: '',
  weapon_caliber_inches: '',
  allowed_slot_types: [],
  sort_order: 100,
  is_active: true,
}

test('bow and stern weapon payloads cannot retain broadside weapon classes', () => {
  const payload = optionPayload({
    ...baseForm,
    option_kind: 'bow_stern',
    weapon_class: 'heavy',
    allowed_slot_types: ['weapon_front', 'weapon_rear'],
  }, {})

  assert.equal(payload.weapon_class, null)
})

test('broadside cannon payloads retain their normalized size class', () => {
  const payload = optionPayload({
    ...baseForm,
    option_kind: 'cannon',
    weapon_class: 'medium',
    allowed_slot_types: ['weapon_port', 'weapon_starboard'],
  }, {})

  assert.equal(payload.weapon_class, 'medium')
})
