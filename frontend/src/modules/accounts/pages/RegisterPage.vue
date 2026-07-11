<script setup>
import { ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { register } = useSession()

const username = ref('')
const displayName = ref('')
const password = ref('')
const isSubmitting = ref(false)
const error = ref('')
const success = ref(false)
const submittedRequest = ref(null)

async function submitRegister() {
  isSubmitting.value = true
  error.value = ''
  success.value = false
  try {
    const response = await register({
      username: username.value,
      display_name: displayName.value,
      password: password.value,
    })
    submittedRequest.value = response.request
    success.value = true
    username.value = ''
    displayName.value = ''
    password.value = ''
  } catch (err) {
    error.value = err.message || t('auth.registerError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section class="auth-page" aria-labelledby="register-title">
    <div class="wire-frame page-frame auth-frame register-frame">
      <section class="wire-section auth-card refined-auth-card register-card">
        <div class="auth-copy register-copy">
          <p class="eyebrow">{{ t('auth.registerEyebrow') }}</p>
          <h1 id="register-title">{{ t('auth.registerTitle') }}</h1>
          <p>{{ t('auth.registerSubtitle') }}</p>

          <div class="register-benefits" :aria-label="t('auth.registerBenefitsLabel')">
            <span>{{ t('auth.registerBenefit.profile') }}</span>
            <span>{{ t('auth.registerBenefit.fleet') }}</span>
            <span>{{ t('auth.registerBenefit.tools') }}</span>
          </div>
        </div>

        <form class="auth-form register-form" @submit.prevent="submitRegister">
          <section class="register-form-section" aria-labelledby="register-account-heading">
            <div class="form-section-heading compact-form-heading">
              <span class="step-marker">01</span>
              <div>
                <h2 id="register-account-heading">{{ t('auth.registerStepAccount') }}</h2>
                <p>{{ t('auth.registerStepAccountHint') }}</p>
              </div>
            </div>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('auth.username') }}</span>
              <input v-model="username" type="text" autocomplete="username" required minlength="3" maxlength="80" :placeholder="t('auth.usernamePlaceholder')" />
              <small>{{ t('auth.usernameHint') }}</small>
            </label>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('profile.displayName') }}</span>
              <input v-model="displayName" type="text" autocomplete="nickname" required maxlength="120" :placeholder="t('auth.displayNamePlaceholder')" />
              <small>{{ t('auth.displayNameHint') }}</small>
            </label>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('auth.password') }}</span>
              <input v-model="password" type="password" autocomplete="new-password" required minlength="12" :placeholder="t('auth.passwordPlaceholder')" />
              <small>{{ t('auth.passwordHint') }}</small>
            </label>
          </section>

          <section class="register-form-section registration-separation-note" aria-labelledby="register-fleet-later-heading">
            <div class="form-section-heading compact-form-heading">
              <span class="step-marker">02</span>
              <div>
                <h2 id="register-fleet-later-heading">{{ t('auth.registerFleetLaterTitle') }}</h2>
                <p>{{ t('auth.registerFleetLaterText') }}</p>
              </div>
            </div>
            <RouterLink class="small-action" to="/fleet">{{ t('common.fleetOverview') }}</RouterLink>
          </section>

          <p v-if="error" class="error-text">{{ error }}</p>
          <div v-if="success" class="success-panel registration-review-panel">
            <strong>{{ t('auth.registerPendingTitle') }}</strong>
            <p>{{ t('auth.registerSuccess') }}</p>
            <small v-if="submittedRequest">{{ t('auth.registerRequestId', { id: submittedRequest.id }) }}</small>
          </div>

          <button class="form-button primary-action register-submit" type="submit" :disabled="isSubmitting">
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
