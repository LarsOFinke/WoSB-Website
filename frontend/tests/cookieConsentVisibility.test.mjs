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
const banner = await readFile(
  new URL('../src/modules/privacy/components/CookieConsentBanner.vue', import.meta.url),
  'utf8',
)

test('missing consent decision opens the cookie dialog automatically', () => {
  assert.match(consentComposable, /state\.visible\s*=\s*!Boolean\(payload\?\.has_decision\)/)
  assert.match(banner, /v-if="state\.visible \|\| state\.loading"/)
})

test('failed consent initialization fails closed and keeps controls reachable', () => {
  const initializationFailure = consentComposable.match(/\.catch\(\(error\) => \{([\s\S]*?)\n    \}\)/)?.[1] || ''
  assert.notEqual(initializationFailure, '')
  assert.match(initializationFailure, /state\.visible\s*=\s*true/)
  assert.match(initializationFailure, /state\.settingsOpen\s*=\s*true/)
})

test('cookie settings remain explicitly accessible', () => {
  assert.match(consentComposable, /function openSettings\(\)[\s\S]*?state\.visible\s*=\s*true/)
  assert.match(consentComposable, /function openSettings\(\)[\s\S]*?initialize\(\{ force: true, revealIfUndecided: false \}\)/)
  assert.match(footer, /@click="openSettings"/)
  assert.match(privacyCenter, /@click="openSettings"/)
})

test('automatic consent refresh cannot hide an explicitly opened dialog', () => {
  assert.match(consentComposable, /if \(revealIfUndecided && !state\.settingsOpen\)/)
})

test('failed cookie settings initialization remains retryable', () => {
  const initializationFailure = consentComposable.match(/\.catch\(\(error\) => \{([\s\S]*?)\n    \}\)/)?.[1] || ''
  assert.match(initializationFailure, /state\.initialized\s*=\s*false/)
})

test('saving always enforces necessary consent and only closes after success', () => {
  assert.match(consentComposable, /saveCookieConsent\(\{ necessary: true, \.\.\.choice \}\)/)
  const persistFailure = consentComposable.match(/async function persist[\s\S]*?catch \(error\) \{([\s\S]*?)\n  \} finally/)?.[1] || ''
  assert.notEqual(persistFailure, '')
  assert.doesNotMatch(persistFailure, /state\.visible\s*=\s*false/)
  assert.doesNotMatch(persistFailure, /state\.settingsOpen\s*=\s*false/)
})
