import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const loginPage = await readFile(new URL('../src/modules/accounts/pages/LoginPage.vue', import.meta.url), 'utf8')
const authMessages = await readFile(new URL('../src/locales/messages/userBuildsAndPassword.js', import.meta.url), 'utf8')
const publicModuleMessages = await readFile(new URL('../src/locales/messages/contentModulesAndBuildStats.js', import.meta.url), 'utf8')
const groupMessages = await readFile(new URL('../src/locales/messages/groupManagement.js', import.meta.url), 'utf8')

test('login page does not expose authentication implementation details', () => {
  assert.doesNotMatch(loginPage, /auth\.sessionHint/)
  assert.doesNotMatch(authMessages, /HttpOnly|\bJWT\b|session cookie|Session-Cookie|simple session|einfachen Session-Login/i)
})

test('public and member-facing copy avoids internal deployment terminology', () => {
  const publicCopy = `${publicModuleMessages}\n${groupMessages}`
  assert.doesNotMatch(publicCopy, /backend file|Backend-Datei|seeded catalog|prototype mode|\bMVP\b/i)
})
