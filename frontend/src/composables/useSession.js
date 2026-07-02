import { computed, ref } from 'vue'

import { authService } from '@/services/authService'

function parseStoredUser() {
  try {
    const storedUser = localStorage.getItem('wosb_user')
    return storedUser ? JSON.parse(storedUser) : null
  } catch {
    localStorage.removeItem('wosb_user')
    return null
  }
}

const user = ref(parseStoredUser())
const token = ref(localStorage.getItem('wosb_access_token'))
const isSessionReady = ref(false)

export function useSession() {
  const isAuthenticated = computed(() => Boolean(user.value && token.value))
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.is_admin === true)

  function setSession(authResponse) {
    user.value = authResponse.user
    token.value = authResponse.access_token
    localStorage.setItem('wosb_user', JSON.stringify(authResponse.user))
    localStorage.setItem('wosb_access_token', authResponse.access_token)
    isSessionReady.value = true
  }

  function clearSession() {
    user.value = null
    token.value = null
    isSessionReady.value = true
    localStorage.removeItem('wosb_user')
    localStorage.removeItem('wosb_access_token')
  }

  async function refreshSession() {
    if (!token.value) {
      clearSession()
      return false
    }

    try {
      const me = await authService.me()
      user.value = me
      localStorage.setItem('wosb_user', JSON.stringify(me))
      isSessionReady.value = true
      return true
    } catch {
      clearSession()
      return false
    }
  }

  return {
    user,
    token,
    isAdmin,
    isAuthenticated,
    isSessionReady,
    setSession,
    clearSession,
    refreshSession,
  }
}
