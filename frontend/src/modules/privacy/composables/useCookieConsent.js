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

function applyState(payload) {
  state.policyVersion = payload?.policy_version || ''
  state.choice = {
    necessary: true,
    preferences: Boolean(payload?.preferences),
    analytics: Boolean(payload?.analytics),
    external_media: Boolean(payload?.external_media),
  }
}

async function initialize() {
  if (state.initialized) return
  if (initializationPromise) return initializationPromise
  state.loading = true
  state.error = ''
  initializationPromise = getCookieConsent()
    .then((payload) => {
      applyState(payload)
      state.initialized = true
    })
    .catch((error) => {
      state.error = error.message || 'Unable to load cookie settings.'
      state.initialized = true
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
  try {
    const payload = await saveCookieConsent({ necessary: true, ...choice })
    applyState(payload)
    state.visible = false
    state.settingsOpen = false
  } catch (error) {
    state.error = error.message || 'Unable to save cookie settings.'
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
