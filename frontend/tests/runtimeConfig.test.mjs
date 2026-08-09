import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const runtimeSource = readFileSync(new URL('../src/config/runtime.js', import.meta.url), 'utf8')

test('production API configuration uses a statically replaceable Vite environment reference', () => {
  assert.match(runtimeSource, /import\.meta\.env\.VITE_API_BASE_URL/)
  assert.doesNotMatch(runtimeSource, /import\.meta\.env\s*\[/)
  assert.match(
    runtimeSource,
    /requireEnvValue\(\s*['"]VITE_API_BASE_URL['"]\s*,\s*import\.meta\.env\.VITE_API_BASE_URL\s*\)/,
  )
})
