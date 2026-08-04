import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const consentComposable = await readFile(
  new URL('../src/modules/privacy/composables/useCookieConsent.js', import.meta.url),
  'utf8',
)
const footer = await readFile(new URL('../src/core/components/AppFooter.vue', import.meta.url), 'utf8')
const privacyCenter = await readFile(
  new URL('../src/modules/privacy/pages/PrivacyCenterPage.vue', import.meta.url),
  'utf8',
)

test('missing consent storage does not open the cookie dialog automatically', () => {
  const initializationFailure = consentComposable.match(/\.catch\(\(error\) => \{([\s\S]*?)\n    \}\)/)?.[1] || ''
  assert.doesNotMatch(consentComposable, /state\.visible\s*=\s*!payload\?\.has_decision/)
  assert.notEqual(initializationFailure, '')
  assert.doesNotMatch(initializationFailure, /state\.visible\s*=\s*true/)
})

test('cookie settings remain explicitly accessible', () => {
  assert.match(consentComposable, /function openSettings\(\)[\s\S]*?state\.visible\s*=\s*true/)
  assert.match(consentComposable, /function openSettings\(\)[\s\S]*?initialize\(\{ force: true \}\)/)
  assert.match(footer, /@click="openSettings"/)
  assert.match(privacyCenter, /@click="openSettings"/)
})

test('failed cookie settings initialization remains retryable', () => {
  const initializationFailure = consentComposable.match(/\.catch\(\(error\) => \{([\s\S]*?)\n    \}\)/)?.[1] || ''
  assert.match(initializationFailure, /state\.initialized\s*=\s*false/)
})
