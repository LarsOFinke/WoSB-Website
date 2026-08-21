import { reactive } from 'vue'

import { getCookieConsent, saveCookieConsent } from '@/modules/privacy/api/cookieConsent'

const defaultChoice = () => ({
  necessary: true,
  preferences: false,
  analytics: false,
  external_media: false,
})

const state = reactive({
  initialized: false,
  loading: false,
  saving: false,
  visible: false,
  settingsOpen: false,
  error: '',
  policyVersion: '',
  choice: defaultChoice(),
})

let initializationPromise = null

function logConsent(event, details = {}) {
  if (import.meta.env?.DEV !== true) return
  if (typeof console === 'undefined' || typeof console.info !== 'function') return
  console.info(`[privacy] cookie_consent_${event}`, details)
}

function applyState(payload, { revealIfUndecided = true } = {}) {
  state.policyVersion = payload?.policy_version || ''
  state.choice = {
    necessary: true,
    preferences: Boolean(payload?.preferences),
    analytics: Boolean(payload?.analytics),
    external_media: Boolean(payload?.external_media),
  }
  // A consent record is the only signal that optional processing was
  // presented and decided. Necessary cookies remain available, but the
  // banner must be shown until the server confirms a decision.
  // An explicit settings request owns visibility. This also protects the
  // button flow from an in-flight automatic initialization response.
  if (revealIfUndecided && !state.settingsOpen) {
    state.visible = !Boolean(payload?.has_decision)
  }
}

async function initialize({ force = false, revealIfUndecided = true } = {}) {
  if (state.initialized && !force) return
  if (initializationPromise) {
    await initializationPromise
    if (!force) return
    if (initializationPromise) return initializationPromise
  }
  state.loading = true
  state.error = ''
  logConsent('initialize_start', { force, revealIfUndecided })
  initializationPromise = getCookieConsent()
    .then((payload) => {
      applyState(payload, { revealIfUndecided })
      state.initialized = true
      logConsent('initialize_complete', {
        hasDecision: Boolean(payload?.has_decision),
        policyVersion: payload?.policy_version || '',
        visible: state.visible,
        settingsOpen: state.settingsOpen,
      })
    })
    .catch((error) => {
      state.error = error.message || 'Unable to load cookie settings.'
      state.initialized = false
      // Fail closed for optional processing and keep the consent controls
      // reachable when the consent endpoint is temporarily unavailable.
      state.visible = true
      state.settingsOpen = true
      logConsent('initialize_failed', {
        status: error.status || 0,
        requestId: error.requestId || '',
        message: state.error,
      })
    })
    .finally(() => {
      state.loading = false
      initializationPromise = null
    })
  return initializationPromise
}

async function persist(choice) {
  state.saving = true
  state.error = ''
  logConsent('save_start', { settingsOpen: state.settingsOpen })
  try {
    const payload = await saveCookieConsent({ necessary: true, ...choice })
    applyState(payload)
    state.visible = false
    state.settingsOpen = false
    logConsent('save_complete', { visible: state.visible })
  } catch (error) {
    state.error = error.message || 'Unable to save cookie settings.'
    logConsent('save_failed', {
      status: error.status || 0,
      requestId: error.requestId || '',
      message: state.error,
    })
  } finally {
    state.saving = false
  }
}

function acceptAll() {
  return persist({ necessary: true, preferences: true, analytics: true, external_media: true })
}

function rejectOptional() {
  return persist(defaultChoice())
}

function saveCustom() {
  return persist(state.choice)
}

function openSettings() {
  state.visible = true
  state.settingsOpen = true
  return initialize({ force: true, revealIfUndecided: false })
}

function toggleSettings() {
  state.settingsOpen = !state.settingsOpen
}

export function useCookieConsent() {
  return {
    state,
    initialize,
    acceptAll,
    rejectOptional,
    saveCustom,
    openSettings,
    toggleSettings,
  }
}
