const RELOAD_MARKER_PREFIX = 'rbf:deployment-chunk-reload:'

const STALE_CHUNK_ERROR_PATTERNS = [
  /failed to fetch dynamically imported module/i,
  /error loading dynamically imported module/i,
  /importing a module script failed/i,
  /failed to load module script/i,
  /loading (?:css )?chunk [\w-]+ failed/i,
  /chunkloaderror/i,
  /preloaderror/i,
]

function errorText(error) {
  return [
    error?.name,
    error?.message,
    error?.cause?.name,
    error?.cause?.message,
    typeof error === 'string' ? error : '',
  ]
    .filter(Boolean)
    .join(' ')
}

function safeRouteTarget(target, location) {
  if (typeof target === 'string' && target.startsWith('/')) return target
  if (!location) return '/'
  return `${location.pathname || '/'}${location.search || ''}${location.hash || ''}`
}

export function isStaleDeploymentChunkError(error) {
  const text = errorText(error)
  return STALE_CHUNK_ERROR_PATTERNS.some((pattern) => pattern.test(text))
}

export function createDeploymentChunkRecovery({
  storage = typeof window !== 'undefined' ? window.sessionStorage : null,
  location = typeof window !== 'undefined' ? window.location : null,
  markerPrefix = RELOAD_MARKER_PREFIX,
} = {}) {
  function markerKey(target) {
    return `${markerPrefix}${safeRouteTarget(target, location)}`
  }

  function reload(error, target) {
    if (!isStaleDeploymentChunkError(error) || !location?.replace || !storage) return false

    const href = safeRouteTarget(target, location)
    const key = markerKey(href)

    try {
      if (storage.getItem(key) === '1') return false
      storage.setItem(key, '1')
    } catch {
      // Do not risk an endless reload loop when session storage is unavailable.
      return false
    }

    location.replace(href)
    return true
  }

  function navigationSucceeded(target) {
    if (!storage) return
    try {
      storage.removeItem(markerKey(target))
    } catch {
      // Storage cleanup is best-effort and must never break navigation.
    }
  }

  return { navigationSucceeded, reload }
}

function browserSessionStorage(browser) {
  try {
    return browser?.sessionStorage || null
  } catch {
    return null
  }
}

function browserRouteTarget(browser) {
  const location = browser?.location
  if (!location) return '/'
  return `${location.pathname || '/'}${location.search || ''}${location.hash || ''}`
}

export function installDeploymentChunkRecovery(router, browser = typeof window !== 'undefined' ? window : null) {
  const recovery = createDeploymentChunkRecovery({
    storage: browserSessionStorage(browser),
    location: browser?.location,
  })

  router.onError((error, to) => {
    const target = to ? router.resolve(to).href : browserRouteTarget(browser)
    if (!recovery.reload(error, target)) {
      console.error('Route module could not be loaded.', error)
    }
  })

  router.afterEach((to) => {
    recovery.navigationSucceeded(router.resolve(to).href)
  })

  if (browser?.addEventListener) {
    browser.addEventListener('vite:preloadError', (event) => {
      const error = event?.payload || event?.detail || event
      const target = browserRouteTarget(browser)
      if (recovery.reload(error, target)) event.preventDefault?.()
    })
  }

  return recovery
}
