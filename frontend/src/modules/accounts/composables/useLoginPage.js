import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

export function useLoginPage() {
  const route = useRoute()
  const router = useRouter()
  const { t } = useLocale()
  const { login } = useSession()

  const username = ref('')
  const password = ref('')
  const isSubmitting = ref(false)
  const error = ref('')

  async function submitLogin() {
    isSubmitting.value = true
    error.value = ''
    try {
      await login(username.value, password.value)
      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/profile'
      router.push(redirect)
    } catch (err) {
      error.value = err.message || t('auth.loginError')
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    route,
    router,
    t,
    login,
    username,
    password,
    isSubmitting,
    error,
    submitLogin,
  }
}
