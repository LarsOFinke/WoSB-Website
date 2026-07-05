<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/services/session'

const router = useRouter()
const { t } = useLocale()
const { register } = useSession()

const username = ref('')
const displayName = ref('')
const fleetName = ref('')
const password = ref('')
const isSubmitting = ref(false)
const error = ref('')
const success = ref(false)

async function submitRegister() {
  isSubmitting.value = true
  error.value = ''
  success.value = false
  try {
    await register({
      username: username.value,
      display_name: displayName.value,
      fleet_name: fleetName.value || null,
      password: password.value,
    })
    success.value = true
    window.setTimeout(() => router.push('/login'), 700)
  } catch (err) {
    error.value = err.message || t('auth.registerError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section class="auth-page" aria-labelledby="register-title">
    <div class="wire-frame page-frame auth-frame">
      <section class="wire-section auth-card refined-auth-card">
        <div class="auth-copy">
          <p class="eyebrow">{{ t('auth.registerEyebrow') }}</p>
          <h1 id="register-title">{{ t('auth.registerTitle') }}</h1>
          <p>{{ t('auth.registerSubtitle') }}</p>
        </div>

        <form class="auth-form" @submit.prevent="submitRegister">
          <label>
            <span>{{ t('auth.username') }}</span>
            <input v-model="username" type="text" autocomplete="username" required minlength="3" maxlength="80" />
          </label>

          <label>
            <span>{{ t('profile.displayName') }}</span>
            <input v-model="displayName" type="text" autocomplete="nickname" required maxlength="120" />
          </label>

          <label>
            <span>{{ t('profile.fleetName') }}</span>
            <input v-model="fleetName" type="text" autocomplete="organization" maxlength="120" />
          </label>

          <label>
            <span>{{ t('auth.password') }}</span>
            <input v-model="password" type="password" autocomplete="new-password" required minlength="6" />
          </label>

          <p v-if="error" class="error-text">{{ error }}</p>
          <p v-if="success" class="success-text">{{ t('auth.registerSuccess') }}</p>

          <button class="form-button primary-action" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? t('auth.creatingAccount') : t('auth.createAccount') }}
          </button>

          <p class="muted auth-hint">
            {{ t('auth.alreadyAccount') }}
            <RouterLink to="/login">{{ t('auth.login') }}</RouterLink>
          </p>
        </form>
      </section>
    </div>
  </section>
</template>
