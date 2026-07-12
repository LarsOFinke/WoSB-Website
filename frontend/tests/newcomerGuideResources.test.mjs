import test from 'node:test'
import assert from 'node:assert/strict'

import { appendLinkedResource } from '../src/modules/onboarding/services/newcomerGuideResources.js'

test('guide and build links reuse a resource block', () => {
  const blocks = []
  const first = appendLinkedResource(blocks, 'guide')
  const second = appendLinkedResource(blocks, 'build')
  assert.equal(first, second)
  assert.equal(blocks.length, 1)
  assert.deepEqual(blocks[0].resources.map((row) => row.resource_type), ['guide', 'build'])
})

test('invalid resource types are ignored', () => {
  const blocks = []
  assert.equal(appendLinkedResource(blocks, 'external'), null)
  assert.deepEqual(blocks, [])
})
