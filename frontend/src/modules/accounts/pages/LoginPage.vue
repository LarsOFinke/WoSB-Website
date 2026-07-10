<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

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
</script>

<template>
  <section class="auth-page" aria-labelledby="login-title">
    <div class="wire-frame page-frame auth-frame polished-auth-frame">
      <section class="wire-section auth-card polished-auth-card">
        <div class="auth-copy polished-auth-copy">
          <p class="eyebrow">{{ t('auth.loginEyebrow') }}</p>
          <h1 id="login-title">{{ t('auth.loginTitle') }}</h1>
          <p>{{ t('auth.loginSubtitle') }}</p>

          <div class="auth-benefit-list" :aria-label="t('auth.loginBenefitsLabel')">
            <span>{{ t('auth.loginBenefits.profile') }}</span>
            <span>{{ t('auth.loginBenefits.myBuilds') }}</span>
            <span>{{ t('auth.loginBenefits.staff') }}</span>
          </div>
        </div>

        <form class="auth-form polished-auth-form" @submit.prevent="submitLogin">
          <label class="input-panel embedded-field">
            <span>{{ t('auth.username') }}</span>
            <input v-model="username" type="text" autocomplete="username" required :placeholder="t('auth.usernamePlaceholder')" />
          </label>

          <label class="input-panel embedded-field">
            <span>{{ t('auth.password') }}</span>
            <input v-model="password" type="password" autocomplete="current-password" required :placeholder="t('auth.passwordPlaceholder')" />
          </label>

          <p v-if="error" class="error-text">{{ error }}</p>

          <button class="form-button primary-action" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? t('auth.signingIn') : t('auth.login') }}
          </button>

          <div class="auth-secondary-actions">
            <p class="muted auth-hint">
              {{ t('auth.noAccount') }}
              <RouterLink to="/register">{{ t('auth.register') }}</RouterLink>
            </p>
            <small class="muted">{{ t('auth.sessionHint') }}</small>
          </div>
        </form>
      </section>
    </div>
  </section>
</template>
