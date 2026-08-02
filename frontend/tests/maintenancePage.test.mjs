import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const source = await readFile(new URL('../public/maintenance.html', import.meta.url), 'utf8')

test('maintenance response is self-contained, responsive and recognizably branded', () => {
  assert.match(source, /Royal Blackwater Fleet/)
  assert.match(source, /HTTP 503/)
  assert.match(source, /Wir sind gleich wieder auf Kurs/)
  assert.match(source, /@media \(max-width: 34rem\)/)
  assert.match(source, /prefers-reduced-motion/)
  assert.doesNotMatch(source, /<(?:script|link)\b/i)
})
