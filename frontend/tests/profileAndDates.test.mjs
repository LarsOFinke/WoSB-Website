import test from 'node:test'
import assert from 'node:assert/strict'

import {
  addPreferenceId,
  removePreferenceId,
  splitPreferenceOptions,
} from '../src/modules/accounts/preferenceTransfer.js'
import {
  isValidDateInput,
  isValidTimeInput,
  localDateTimeValue,
  splitLocalDateTime,
} from '../src/shared/datetime/localDateTime.js'


test('preferred ships move between available and selected collections', () => {
  const options = [{ id: 1, name: 'Anson' }, { id: 2, name: 'Victory' }]
  const selected = addPreferenceId([], 2)
  const split = splitPreferenceOptions(options, selected)

  assert.deepEqual(split.selectedOptions, [{ id: 2, name: 'Victory' }])
  assert.deepEqual(split.availableOptions, [{ id: 1, name: 'Anson' }])
  assert.deepEqual(removePreferenceId(selected, 2), [])
})


test('date and time fields reject concatenated malformed years', () => {
  assert.equal(isValidDateInput('12.07.202612'), false)
  assert.equal(isValidDateInput('2026-07-12'), true)
  assert.equal(isValidDateInput('2026-02-30'), false)
  assert.equal(isValidTimeInput('23:23'), true)
  assert.equal(localDateTimeValue('2026-07-12', '23:23'), '2026-07-12T23:23')
  assert.deepEqual(splitLocalDateTime('2026-07-12T23:23'), {
    date: '2026-07-12',
    time: '23:23',
  })
})
