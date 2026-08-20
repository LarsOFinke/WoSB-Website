import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

test('protected routes require an authenticated session before role checks', async () => {
  const source = await readFile(new URL('../src/router/index.js', import.meta.url), 'utf8')
  const authGuard = source.indexOf('(to.meta.requiresUser || to.meta.requiresStaff || to.meta.requiresContentAuthor || to.meta.requiresAdmin || to.meta.requiresFleetManagement) && !isAuthenticated.value')
  const contentAuthorGuard = source.indexOf('to.meta.requiresContentAuthor && !canAuthorContent.value')
  const adminGuard = source.indexOf('to.meta.requiresAdmin && !isAdmin.value')
  const staffGuard = source.indexOf('to.meta.requiresStaff && !isStaff.value')
  assert.ok(authGuard >= 0)
  assert.ok(adminGuard > authGuard)
  assert.ok(staffGuard > authGuard)
  assert.ok(contentAuthorGuard > authGuard)
})

test('frontend route guards remain defense in depth rather than authorization authority', async () => {
  const source = await readFile(new URL('../src/router/index.js', import.meta.url), 'utf8')
  assert.match(source, /await loadSession\(\)/)
  assert.match(source, /requiresFleetManagement/)
  assert.match(source, /requiresContentAuthor/)
})

test('shared-content editors are staff-only while member list and self-service routes stay available', async () => {
  const session = await readFile(new URL('../src/modules/accounts/session.js', import.meta.url), 'utf8')
  assert.match(session, /const canAuthorContent = computed\(\(\) => isStaff\.value\)/)
  assert.match(session, /const canManageFleet = computed\(\(\) => isStaff\.value\)/)

  const routeFiles = [
    'builds', 'calendar', 'forum', 'groups', 'guides', 'strategy-planner',
  ]
  for (const moduleName of routeFiles) {
    const routes = await readFile(new URL(`../src/modules/${moduleName}/routes.js`, import.meta.url), 'utf8')
    assert.match(routes, /requiresContentAuthor: true/, `${moduleName} must protect authoring routes`)
    assert.match(routes, /requiresUser: true/, `${moduleName} must retain member read routes`)
  }

  const profileRoutes = await readFile(new URL('../src/modules/accounts/routes.js', import.meta.url), 'utf8')
  const fleetRoutes = await readFile(new URL('../src/modules/fleet/routes.js', import.meta.url), 'utf8')
  assert.match(profileRoutes, /requiresUser: true/)
  assert.match(fleetRoutes, /path: '\/fleet'/)
})
