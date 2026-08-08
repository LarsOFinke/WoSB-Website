import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import { MAX_DOCUMENT_BYTES, MAX_IMAGE_BYTES, MAX_UPLOAD_BYTES } from '../src/modules/files/fileTypes.js'

test('upload limits mirror the backend transport envelope', () => {
  assert.equal(MAX_IMAGE_BYTES, 12 * 1024 * 1024)
  assert.equal(MAX_DOCUMENT_BYTES, 24 * 1024 * 1024)
  assert.equal(MAX_UPLOAD_BYTES, 50 * 1024 * 1024)
})

test('upload preflight rejects control and bidi filenames before transport', async () => {
  const source = await readFile(new URL('../src/modules/files/api/files.js', import.meta.url), 'utf8')
  assert.match(source, /hasUnsafeFilename/)
  assert.match(source, /\\u202a-\\u202e/)
  assert.match(source, /reason: 'name'/)
})
