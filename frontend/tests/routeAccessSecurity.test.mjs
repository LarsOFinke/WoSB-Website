import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

test('protected routes require an authenticated session before role checks', async () => {
  const source = await readFile(new URL('../src/router/index.js', import.meta.url), 'utf8')
  const authGuard = source.indexOf('(to.meta.requiresUser || to.meta.requiresStaff || to.meta.requiresAdmin || to.meta.requiresFleetManagement) && !isAuthenticated.value')
  const adminGuard = source.indexOf('to.meta.requiresAdmin && !isAdmin.value')
  const staffGuard = source.indexOf('to.meta.requiresStaff && !isStaff.value')
  assert.ok(authGuard >= 0)
  assert.ok(adminGuard > authGuard)
  assert.ok(staffGuard > authGuard)
})

test('frontend route guards remain defense in depth rather than authorization authority', async () => {
  const source = await readFile(new URL('../src/router/index.js', import.meta.url), 'utf8')
  assert.match(source, /await loadSession\(\)/)
  assert.match(source, /requiresFleetManagement/)
})
