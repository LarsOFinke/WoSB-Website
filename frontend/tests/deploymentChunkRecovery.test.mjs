import assert from 'node:assert/strict'
import test from 'node:test'

import {
  createDeploymentChunkRecovery,
  installDeploymentChunkRecovery,
  isStaleDeploymentChunkError,
} from '../src/core/navigation/deploymentChunkRecovery.js'

function fakeStorage() {
  const values = new Map()
  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null
    },
    removeItem(key) {
      values.delete(key)
    },
    setItem(key, value) {
      values.set(key, value)
    },
  }
}

test('recognizes stale deployment chunk failures without treating generic network errors as chunks', () => {
  assert.equal(
    isStaleDeploymentChunkError(new TypeError('Failed to fetch dynamically imported module: /assets/MyBuilds-OLD.js')),
    true,
  )
  assert.equal(isStaleDeploymentChunkError(new Error('ChunkLoadError: Loading chunk 42 failed')), true)
  assert.equal(isStaleDeploymentChunkError(new Error('API request failed with status 503')), false)
  assert.equal(isStaleDeploymentChunkError(new TypeError('Failed to fetch')), false)
})

test('reloads the intended route once and clears the guard after successful navigation', () => {
  const replacements = []
  const storage = fakeStorage()
  const recovery = createDeploymentChunkRecovery({
    storage,
    location: {
      pathname: '/builds',
      search: '',
      hash: '',
      replace(href) {
        replacements.push(href)
      },
    },
  })
  const error = new TypeError('Failed to fetch dynamically imported module')

  assert.equal(recovery.reload(error, '/profile/builds'), true)
  assert.deepEqual(replacements, ['/profile/builds'])

  assert.equal(recovery.reload(error, '/profile/builds'), false)
  assert.deepEqual(replacements, ['/profile/builds'])

  recovery.navigationSucceeded('/profile/builds')
  assert.equal(recovery.reload(error, '/profile/builds'), true)
  assert.deepEqual(replacements, ['/profile/builds', '/profile/builds'])
})

test('does not reload when session storage cannot provide a loop guard', () => {
  let replacement = null
  const recovery = createDeploymentChunkRecovery({
    storage: {
      getItem() {
        throw new Error('storage disabled')
      },
      setItem() {},
      removeItem() {},
    },
    location: {
      pathname: '/',
      search: '',
      hash: '',
      replace(href) {
        replacement = href
      },
    },
  })

  assert.equal(recovery.reload(new Error('Importing a module script failed'), '/profile'), false)
  assert.equal(replacement, null)
})

test('router integration reloads the failed lazy destination and clears it after navigation', () => {
  const hooks = {}
  const replacements = []
  const browser = {
    sessionStorage: fakeStorage(),
    location: {
      pathname: '/builds',
      search: '?sort=recent',
      hash: '',
      replace(href) {
        replacements.push(href)
      },
    },
    addEventListener(name, handler) {
      hooks[name] = handler
    },
  }
  const router = {
    afterEach(handler) {
      hooks.afterEach = handler
    },
    onError(handler) {
      hooks.onError = handler
    },
    resolve(route) {
      return { href: route.fullPath }
    },
  }

  installDeploymentChunkRecovery(router, browser)
  hooks.onError(new Error('Failed to fetch dynamically imported module'), { fullPath: '/profile/builds' })
  assert.deepEqual(replacements, ['/profile/builds'])

  hooks.afterEach({ fullPath: '/profile/builds' })
  hooks.onError(new Error('Failed to fetch dynamically imported module'), { fullPath: '/profile/builds' })
  assert.deepEqual(replacements, ['/profile/builds', '/profile/builds'])

  let prevented = false
  hooks['vite:preloadError']({
    payload: new Error('Importing a module script failed'),
    preventDefault() {
      prevented = true
    },
  })
  assert.equal(prevented, true)
  assert.equal(replacements.at(-1), '/builds?sort=recent')
})
