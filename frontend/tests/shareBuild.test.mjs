import test from 'node:test'
import assert from 'node:assert/strict'

import { buildShareUrl, copyBuildShareLink } from '../src/modules/builds/shareBuild.js'

test('build share link points to the public build detail route', async () => {
  const location = { origin: 'https://fleet.example' }
  assert.equal(buildShareUrl(42, location), 'https://fleet.example/builds/42')
  let copied = ''
  const result = await copyBuildShareLink(42, {
    location,
    clipboard: { writeText: async (value) => { copied = value } },
  })
  assert.equal(result, 'https://fleet.example/builds/42')
  assert.equal(copied, result)
})
