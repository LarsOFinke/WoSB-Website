<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/services/session'
import { listFleets } from '@/services/fleets'

const router = useRouter()
const { t } = useLocale()
const { register } = useSession()

const username = ref('')
const displayName = ref('')
const fleetName = ref('')
const fleetId = ref('')
const fleetApplicationNote = ref('')
const fleets = ref([])
const password = ref('')
const isSubmitting = ref(false)
const error = ref('')
const success = ref(false)

const selectedFleet = computed(() => fleets.value.find((fleet) => String(fleet.id) === fleetId.value) || null)

async function submitRegister() {
  isSubmitting.value = true
  error.value = ''
  success.value = false
  try {
    await register({
      username: username.value,
      display_name: displayName.value,
      fleet_name: fleetName.value || null,
      fleet_id: fleetId.value ? Number(fleetId.value) : null,
      fleet_application_note: fleetApplicationNote.value || null,
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

onMounted(async () => {
  try {
    fleets.value = await listFleets()
  } catch {
    fleets.value = []
  }
})
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
              <input v-model="password" type="password" autocomplete="new-password" required minlength="6" :placeholder="t('auth.passwordPlaceholder')" />
              <small>{{ t('auth.passwordHint') }}</small>
            </label>
          </section>

          <section class="register-form-section" aria-labelledby="register-fleet-heading">
            <div class="form-section-heading compact-form-heading">
              <span class="step-marker">02</span>
              <div>
                <h2 id="register-fleet-heading">{{ t('auth.registerStepFleet') }}</h2>
                <p>{{ t('auth.registerStepFleetHint') }}</p>
              </div>
            </div>

            <label class="input-panel elevated-input-panel select-field-panel">
              <span>{{ t('auth.fleetChoice') }}</span>
              <select v-model="fleetId" autocomplete="organization">
                <option value="">{{ t('fleets.registration.noFleet') }}</option>
                <option v-for="fleet in fleets" :key="fleet.id" :value="String(fleet.id)">{{ fleet.name }}</option>
              </select>
              <small class="field-hint">{{ t('fleets.registration.applicationHint') }}</small>
            </label>

            <article v-if="selectedFleet" class="selected-fleet-preview">
              <span class="summary-pill">{{ t(`fleets.focus.${selectedFleet.focus}`) }}</span>
              <strong>{{ selectedFleet.name }}</strong>
              <p>{{ selectedFleet.description || t('fleets.noDescription') }}</p>
            </article>

            <label v-if="fleetId" class="input-panel elevated-input-panel textarea-input-panel">
              <span>{{ t('auth.fleetApplicationNote') }}</span>
              <textarea v-model="fleetApplicationNote" rows="4" maxlength="1000" :placeholder="t('auth.fleetApplicationNotePlaceholder')"></textarea>
              <small>{{ t('auth.fleetApplicationNoteHint') }}</small>
            </label>

            <label v-else class="input-panel elevated-input-panel">
              <span>{{ t('fleets.registration.freeTextFleet') }}</span>
              <input v-model="fleetName" type="text" autocomplete="organization" maxlength="120" :placeholder="t('auth.freeFleetPlaceholder')" />
              <small>{{ t('auth.freeFleetHint') }}</small>
            </label>
          </section>

          <p v-if="error" class="error-text">{{ error }}</p>
          <p v-if="success" class="success-text">{{ t('auth.registerSuccess') }}</p>

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
