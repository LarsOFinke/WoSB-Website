import { computed, reactive } from 'vue'

import { getCurrentUser, login as loginRequest, logout as logoutRequest, register as registerRequest } from './auth'

const state = reactive({
  user: null,
  isReady: false,
  isLoading: false,
})

export async function loadSession() {
  state.isLoading = true
  try {
    state.user = await getCurrentUser()
  } catch {
    state.user = null
  } finally {
    state.isReady = true
    state.isLoading = false
  }
  return state.user
}

export async function login(username, password) {
  const payload = await loginRequest(username, password)
  state.user = payload.user
  state.isReady = true
  return state.user
}

export async function register(payload) {
  const response = await registerRequest(payload)
  state.isReady = true
  state.user = null
  return response
}

export async function logout() {
  try {
    await logoutRequest()
  } finally {
    state.user = null
    state.isReady = true
  }
}

export function setSessionUser(user) {
  state.user = user
  state.isReady = true
}

export function useSession() {
  return {
    sessionState: state,
    user: computed(() => state.user),
    isAuthenticated: computed(() => Boolean(state.user)),
    isAdmin: computed(() => state.user?.role === 'admin'),
    isModerator: computed(() => state.user?.role === 'moderator'),
    isStaff: computed(() => ['admin', 'moderator'].includes(state.user?.role)),
    loadSession,
    login,
    register,
    logout,
    setSessionUser,
  }
}
