<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { changePassword } from '@/services/auth'
import { listMyFleetMemberships } from '@/services/fleets'
import { getProfile, updateProfile } from '@/services/profile'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { setSessionUser } = useSession()

const loading = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const error = ref('')
const success = ref('')
const passwordError = ref('')
const passwordSuccess = ref('')
const fleetMemberships = ref([])

const activeFleetMemberships = computed(() => fleetMemberships.value.filter((membership) => ['active', 'pending'].includes(membership.status)))
const leadershipMemberships = computed(() => fleetMemberships.value.filter((membership) => membership.status === 'active' && ['fleet_admiral', 'fleet_lieutenant'].includes(membership.role)))

const focusOptions = [
  'pve_farming',
  'pve_imp_hunting',
  'pve_general',
  'pvp_open_world',
  'pvp_arena',
  'pvp_general',
  'trading',
  'other',
]

const form = reactive({
  username: '',
  display_name: '',
  fleet_name: '',
  preferred_focus: '',
  note: '',
  role: 'user',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  repeat_password: '',
})

function fillForm(user) {
  form.username = user.username || ''
  form.display_name = user.display_name || ''
  form.fleet_name = user.fleet_name || ''
  form.preferred_focus = user.preferred_focus || ''
  form.note = user.note || ''
  form.role = user.role || 'user'
}

async function loadMemberships() {
  try {
    fleetMemberships.value = await listMyFleetMemberships()
  } catch {
    fleetMemberships.value = []
  }
}

async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    fillForm(await getProfile())
    await loadMemberships()
  } catch (err) {
    error.value = err.message || t('profile.loadError')
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const updated = await updateProfile({
      display_name: form.display_name,
      fleet_name: form.fleet_name || null,
      preferred_focus: form.preferred_focus || null,
      note: form.note || null,
    })
    fillForm(updated)
    setSessionUser(updated)
    success.value = t('profile.saved')
  } catch (err) {
    error.value = err.message || t('profile.saveError')
  } finally {
    saving.value = false
  }
}

async function submitPasswordChange() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (passwordForm.new_password !== passwordForm.repeat_password) {
    passwordError.value = t('profile.password.repeatMismatch')
    return
  }

  changingPassword.value = true
  try {
    await changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.repeat_password = ''
    passwordSuccess.value = t('profile.password.changed')
  } catch (err) {
    passwordError.value = err.message || t('profile.password.changeError')
  } finally {
    changingPassword.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <section class="profile-page" aria-labelledby="profile-title">
    <div class="wire-frame page-frame profile-frame profile-dashboard-frame">
      <header class="wire-section profile-hero refined-profile-hero">
        <div>
          <p class="eyebrow">{{ t('profile.eyebrow') }}</p>
          <h1 id="profile-title">{{ t('profile.title') }}</h1>
          <p>{{ t('profile.subtitle') }}</p>
        </div>
        <RouterLink class="button-box primary-action" to="/profile/builds">{{ t('myBuilds.title') }}</RouterLink>
      </header>

      <div class="profile-dashboard-grid">
        <section class="wire-section profile-panel profile-account-panel">
          <p v-if="loading" class="muted">{{ t('profile.loading') }}</p>
          <form v-else class="profile-form" @submit.prevent="saveProfile">
            <div class="profile-summary-card refined-summary-card">
              <span>{{ t('profile.account') }}</span>
              <strong>{{ form.username }}</strong>
              <small>{{ t(`roles.${form.role}`) }}</small>
            </div>

            <section class="profile-fleet-card">
              <div>
                <p class="eyebrow">{{ t('profile.fleetMemberships.eyebrow') }}</p>
                <h2>{{ t('profile.fleetMemberships.title') }}</h2>
                <p>{{ t('profile.fleetMemberships.subtitle') }}</p>
              </div>
              <div v-if="activeFleetMemberships.length" class="profile-membership-list">
                <article v-for="membership in activeFleetMemberships" :key="membership.id" class="profile-membership-row">
                  <div>
                    <strong>{{ membership.fleet.name }}</strong>
                    <span>{{ t(`fleets.focus.${membership.fleet.focus}`) }}</span>
                  </div>
                  <div class="member-pill-row">
                    <span class="summary-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
                    <span class="summary-pill">{{ t(`fleets.roles.${membership.role}`) }}</span>
                  </div>
                </article>
              </div>
              <p v-else class="muted">{{ t('profile.fleetMemberships.empty') }}</p>
              <div class="form-actions compact-actions">
                <RouterLink class="button-box" to="/fleets">{{ t('profile.fleetMemberships.browse') }}</RouterLink>
                <RouterLink v-if="leadershipMemberships.length" class="button-box primary-action" to="/fleets/manage">{{ t('profile.fleetMemberships.manage') }}</RouterLink>
              </div>
            </section>

            <label class="input-panel embedded-field">
              <span>{{ t('profile.displayName') }}</span>
              <input v-model="form.display_name" required maxlength="120" />
            </label>

            <label class="input-panel embedded-field">
              <span>{{ t('profile.fleetName') }}</span>
              <input v-model="form.fleet_name" maxlength="120" :placeholder="t('profile.fleetPlaceholder')" />
            </label>

            <label class="input-panel embedded-field">
              <span>{{ t('profile.preferredFocus') }}</span>
              <select v-model="form.preferred_focus">
                <option value="">{{ t('profile.noPreferredFocus') }}</option>
                <option v-for="focus in focusOptions" :key="focus" :value="focus">
                  {{ t(`focus.${focus}`) }}
                </option>
              </select>
            </label>

            <label class="input-panel embedded-field profile-note-field">
              <span>{{ t('profile.note') }}</span>
              <textarea v-model="form.note" maxlength="1000" rows="5" :placeholder="t('profile.notePlaceholder')"></textarea>
            </label>

            <p v-if="error" class="error-text profile-message">{{ error }}</p>
            <p v-if="success" class="success-text profile-message">{{ success }}</p>

            <div class="form-actions profile-actions">
              <button class="wire-section form-button primary" type="submit" :disabled="saving">
                {{ saving ? t('profile.saving') : t('profile.save') }}
              </button>
            </div>
          </form>
        </section>

        <aside class="profile-side-stack">
          <section class="wire-section profile-panel profile-builds-panel">
            <p class="eyebrow">{{ t('myBuilds.eyebrow') }}</p>
            <h2>{{ t('myBuilds.profileCardTitle') }}</h2>
            <p>{{ t('myBuilds.profileCardText') }}</p>
            <RouterLink class="button-box" to="/profile/builds">{{ t('myBuilds.open') }}</RouterLink>
          </section>


          <section class="wire-section profile-panel profile-groups-panel">
            <p class="eyebrow">{{ t('myGroups.eyebrow') }}</p>
            <h2>{{ t('myGroups.profileCardTitle') }}</h2>
            <p>{{ t('myGroups.profileCardText') }}</p>
            <RouterLink class="button-box" to="/profile/groups">{{ t('myGroups.open') }}</RouterLink>
          </section>

          <section class="wire-section profile-panel password-panel">
            <p class="eyebrow">{{ t('profile.password.eyebrow') }}</p>
            <h2>{{ t('profile.password.title') }}</h2>
            <p>{{ t('profile.password.subtitle') }}</p>

            <form class="password-form" @submit.prevent="submitPasswordChange">
              <label class="input-panel embedded-field">
                <span>{{ t('profile.password.current') }}</span>
                <input v-model="passwordForm.current_password" type="password" autocomplete="current-password" required />
              </label>
              <label class="input-panel embedded-field">
                <span>{{ t('profile.password.new') }}</span>
                <input v-model="passwordForm.new_password" type="password" autocomplete="new-password" required minlength="6" />
              </label>
              <label class="input-panel embedded-field">
                <span>{{ t('profile.password.repeat') }}</span>
                <input v-model="passwordForm.repeat_password" type="password" autocomplete="new-password" required minlength="6" />
              </label>

              <p v-if="passwordError" class="error-text profile-message">{{ passwordError }}</p>
              <p v-if="passwordSuccess" class="success-text profile-message">{{ passwordSuccess }}</p>

              <button class="form-button" type="submit" :disabled="changingPassword">
                {{ changingPassword ? t('profile.password.saving') : t('profile.password.save') }}
              </button>
            </form>
          </section>
        </aside>
      </div>
    </div>
  </section>
</template>
