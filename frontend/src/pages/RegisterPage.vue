<script setup>
import { computed, onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/services/session'
import { getOfficialFleet } from '@/services/fleets'

const { t } = useLocale()
const { register } = useSession()

const username = ref('')
const displayName = ref('')
const password = ref('')
const officialFleet = ref(null)
const wantsFleetMembership = ref(false)
const fleetApplicationNote = ref('')
const fleetAvailability = ref('')
const fleetPreferredShips = ref('')
const fleetTimezone = ref('')
const fleetDiscordHandle = ref('')
const isSubmitting = ref(false)
const error = ref('')
const success = ref(false)
const submittedRequest = ref(null)

const selectedFleet = computed(() => wantsFleetMembership.value ? officialFleet.value : null)

async function submitRegister() {
  isSubmitting.value = true
  error.value = ''
  success.value = false
  try {
    const response = await register({
      username: username.value,
      display_name: displayName.value,
      fleet_name: null,
      fleet_id: wantsFleetMembership.value && officialFleet.value ? Number(officialFleet.value.id) : null,
      wants_fleet_membership: wantsFleetMembership.value,
      fleet_application_note: wantsFleetMembership.value ? fleetApplicationNote.value || null : null,
      fleet_availability: wantsFleetMembership.value ? fleetAvailability.value || null : null,
      fleet_preferred_ships: wantsFleetMembership.value ? fleetPreferredShips.value || null : null,
      fleet_timezone: wantsFleetMembership.value ? fleetTimezone.value || null : null,
      fleet_discord_handle: wantsFleetMembership.value ? fleetDiscordHandle.value || null : null,
      password: password.value,
    })
    submittedRequest.value = response.request
    success.value = true
    username.value = ''
    displayName.value = ''
    password.value = ''
    wantsFleetMembership.value = false
    fleetApplicationNote.value = ''
    fleetAvailability.value = ''
    fleetPreferredShips.value = ''
    fleetTimezone.value = ''
    fleetDiscordHandle.value = ''
  } catch (err) {
    error.value = err.message || t('auth.registerError')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  try {
    officialFleet.value = await getOfficialFleet()
  } catch {
    officialFleet.value = null
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

            <label class="input-panel elevated-input-panel fleet-membership-toggle">
              <span>{{ t('auth.joinOfficialFleet') }}</span>
              <div class="checkbox-card-control">
                <input v-model="wantsFleetMembership" type="checkbox" :disabled="!officialFleet" />
                <strong>{{ officialFleet?.name || t('fleets.manage.noFleet') }}</strong>
              </div>
              <small class="field-hint">{{ t('fleets.registration.applicationHint') }}</small>
            </label>

            <article v-if="selectedFleet" class="selected-fleet-preview">
              <span class="summary-pill">{{ t('fleets.singleBadge') }}</span>
              <strong>{{ selectedFleet.name }}</strong>
              <p>{{ selectedFleet.description || t('fleets.noDescription') }}</p>
            </article>

            <div v-if="wantsFleetMembership" class="directory-form-grid register-directory-grid">
              <label class="input-panel elevated-input-panel textarea-input-panel directory-note-field">
                <span>{{ t('auth.fleetApplicationNote') }}</span>
                <textarea v-model="fleetApplicationNote" rows="4" maxlength="1000" :placeholder="t('auth.fleetApplicationNotePlaceholder')"></textarea>
                <small>{{ t('auth.fleetApplicationNoteHint') }}</small>
              </label>
              <label class="input-panel elevated-input-panel">
                <span>{{ t('fleets.directory.availability') }}</span>
                <input v-model="fleetAvailability" maxlength="240" :placeholder="t('fleets.directory.availabilityPlaceholder')" />
              </label>
              <label class="input-panel elevated-input-panel">
                <span>{{ t('fleets.directory.preferredShips') }}</span>
                <input v-model="fleetPreferredShips" maxlength="300" :placeholder="t('fleets.directory.preferredShipsPlaceholder')" />
              </label>
              <label class="input-panel elevated-input-panel">
                <span>{{ t('fleets.directory.timezone') }}</span>
                <input v-model="fleetTimezone" maxlength="80" placeholder="CET / UTC+1" />
              </label>
              <label class="input-panel elevated-input-panel">
                <span>{{ t('fleets.directory.discord') }}</span>
                <input v-model="fleetDiscordHandle" maxlength="120" placeholder="Captain#1234" />
              </label>
            </div>
          </section>

          <p v-if="error" class="error-text">{{ error }}</p>
          <div v-if="success" class="success-panel registration-review-panel"><strong>{{ t('auth.registerPendingTitle') }}</strong><p>{{ t('auth.registerSuccess') }}</p><small v-if="submittedRequest">{{ t('auth.registerRequestId', { id: submittedRequest.id }) }}</small></div>

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
