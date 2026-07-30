import assert from 'node:assert/strict'
import test from 'node:test'

import { calculatePickerPlacement } from '../src/modules/builds/domain/pickerPlacement.js'

test('picker opens below its trigger when there is enough viewport space', () => {
  const placement = calculatePickerPlacement(
    { left: 120, top: 100, bottom: 146, width: 260 },
    { width: 1280, height: 900 },
  )

  assert.equal(placement.placement, 'bottom')
  assert.equal(placement.top, 152)
  assert.equal(placement.bottom, null)
  assert.equal(placement.width, 384)
  assert.equal(placement.left, 120)
  assert.equal(placement.maxHeight, 384)
})

test('picker flips above its trigger near the viewport bottom', () => {
  const placement = calculatePickerPlacement(
    { left: 760, top: 720, bottom: 766, width: 300 },
    { width: 1280, height: 800 },
  )

  assert.equal(placement.placement, 'top')
  assert.equal(placement.top, null)
  assert.equal(placement.bottom, 86)
  assert.equal(placement.maxHeight, 384)
})

test('picker remains inside the horizontal viewport', () => {
  const placement = calculatePickerPlacement(
    { left: 1180, top: 100, bottom: 146, width: 440 },
    { width: 1280, height: 900 },
  )

  assert.equal(placement.width, 440)
  assert.equal(placement.left, 824)
})
