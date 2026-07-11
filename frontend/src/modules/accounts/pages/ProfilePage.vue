<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { changePassword } from '@/modules/accounts/api/auth'
import { getProfile, getProfilePreferenceOptions, updateProfile } from '@/modules/accounts/api/profile'
import { useSession } from '@/modules/accounts/session'
import { listMyFleetMemberships } from '@/modules/fleet/api/fleet'
import PreferenceTransferList from '@/modules/accounts/components/PreferenceTransferList.vue'

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
const preferenceOptions = reactive({ ships: [], roles: [] })

const activeFleetMemberships = computed(() => fleetMemberships.value.filter((membership) => ['active', 'pending'].includes(membership.status)))
const leadershipMemberships = computed(() => fleetMemberships.value.filter((membership) => membership.status === 'active' && ['fleet_admiral', 'fleet_lieutenant'].includes(membership.role)))
const primaryFleetMembership = computed(() => {
  if (!form.fleet_membership_id) return null
  return fleetMemberships.value.find((membership) => membership.id === form.fleet_membership_id) || null
})
const hasOfficialFleetLink = computed(() => Boolean(form.fleet_id && form.fleet_membership_status))
const displayInitials = computed(() => {
  const source = (form.display_name || form.username || 'RBF').trim().split(/\s+/).filter(Boolean)
  return source.slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'RBF'
})
const preferredFocusLabel = computed(() => form.preferred_focus ? t(`focus.${form.preferred_focus}`) : t('profile.noPreferredFocus'))
const preferredShipOptions = computed(() => preferenceOptions.ships.map((ship) => ({
  id: ship.id,
  label: `${ship.name} · Rate ${ship.rate}`,
})))
const preferredRoleOptions = computed(() => preferenceOptions.roles.map((role) => ({
  id: role.id,
  label: role.label,
})))
const fleetStatusLabel = computed(() => hasOfficialFleetLink.value ? t(`fleets.status.${form.fleet_membership_status}`) : t('profile.fleetMemberships.empty'))
const profileCompletion = computed(() => {
  const checks = [
    Boolean(form.display_name.trim()),
    Boolean(form.preferred_focus),
    Boolean(form.note.trim()),
    Boolean(form.timezone.trim() || form.availability.trim()),
    Boolean(form.preferred_ship_ids.length || form.preferred_role_ids.length),
    hasOfficialFleetLink.value || Boolean(form.fleet_name.trim()),
  ]
  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
})
const profileCompletionHint = computed(() => profileCompletion.value === 100
  ? t('profile.completion.complete')
  : t('profile.completion.hint'))

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
  fleet_id: null,
  fleet_membership_id: null,
  fleet_membership_status: '',
  fleet_membership_role: '',
  preferred_focus: '',
  availability: '',
  timezone: '',
  discord_handle: '',
  preferred_ship_ids: [],
  preferred_role_ids: [],
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
  form.fleet_id = user.fleet_id || null
  form.fleet_membership_id = user.fleet_membership_id || null
  form.fleet_membership_status = user.fleet_membership_status || ''
  form.fleet_membership_role = user.fleet_membership_role || ''
  form.preferred_focus = user.preferred_focus || ''
  form.availability = user.availability || ''
  form.timezone = user.timezone || ''
  form.discord_handle = user.discord_handle || ''
  form.preferred_ship_ids = [...(user.preferred_ship_ids || [])]
  form.preferred_role_ids = [...(user.preferred_role_ids || [])]
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
    const [profile, options] = await Promise.all([getProfile(), getProfilePreferenceOptions()])
    fillForm(profile)
    preferenceOptions.ships = options.ships || []
    preferenceOptions.roles = options.roles || []
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
      fleet_name: hasOfficialFleetLink.value ? null : form.fleet_name || null,
      preferred_focus: form.preferred_focus || null,
      availability: form.availability || null,
      timezone: form.timezone || null,
      discord_handle: form.discord_handle || null,
      preferred_ship_ids: form.preferred_ship_ids,
      preferred_role_ids: form.preferred_role_ids,
      note: form.note || null,
    })
    fillForm(updated)
    await loadMemberships()
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
    <div class="wire-frame page-frame profile-frame profile-workspace-frame">
      <PageHeader
        :eyebrow="t('profile.eyebrow')"
        :title="t('profile.title')"
        :description="t('profile.subtitle')"
        title-id="profile-title"
      >
        <template #meta>
          <div class="profile-identity-chip">
            <span class="profile-avatar" aria-hidden="true">{{ displayInitials }}</span>
            <span><strong>{{ form.display_name || form.username }}</strong><small>@{{ form.username }}</small></span>
          </div>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/profile/builds">{{ t('myBuilds.title') }}</RouterLink>
          <RouterLink class="button-box" to="/profile/groups">{{ t('myGroups.title') }}</RouterLink>
          <RouterLink class="button-box primary-action" to="/profile/squads">{{ t('mySquads.title') }}</RouterLink>
        </template>
      </PageHeader>

      <p v-if="loading" class="muted table-state">{{ t('profile.loading') }}</p>

      <template v-else>
        <section class="workspace-metric-grid profile-metric-grid" :aria-label="t('profile.title')">
          <MetricCard :label="t('profile.account')" :value="t(`roles.${form.role}`)" :hint="form.username" />
          <MetricCard :label="t('profile.fleetMemberships.title')" :value="fleetStatusLabel" :hint="form.fleet_name || t('fleets.title')" tone="accent" />
          <MetricCard :label="t('profile.preferredFocus')" :value="preferredFocusLabel" />
          <MetricCard :label="t('profile.completion.label')" :value="`${profileCompletion}%`" :hint="profileCompletionHint" />
        </section>

        <div class="profile-workspace-grid">
          <form class="wire-section profile-editor-panel" @submit.prevent="saveProfile">
            <div class="workspace-section-heading">
              <div>
                <p class="eyebrow">{{ t('profile.account') }}</p>
                <h2>{{ t('profile.displayName') }}</h2>
                <p>{{ t('profile.subtitle') }}</p>
              </div>
              <span class="summary-pill">{{ t(`roles.${form.role}`) }}</span>
            </div>

            <div class="profile-field-grid">
              <label class="input-panel embedded-field">
                <span>{{ t('profile.displayName') }}</span>
                <input v-model="form.display_name" required maxlength="120" />
              </label>

              <label class="input-panel embedded-field">
                <span>{{ t('profile.preferredFocus') }}</span>
                <select v-model="form.preferred_focus">
                  <option value="">{{ t('profile.noPreferredFocus') }}</option>
                  <option v-for="focus in focusOptions" :key="focus" :value="focus">{{ t(`focus.${focus}`) }}</option>
                </select>
              </label>

              <label v-if="!hasOfficialFleetLink" class="input-panel embedded-field profile-field-wide">
                <span>{{ t('profile.externalFleetName') }}</span>
                <input v-model="form.fleet_name" maxlength="120" :placeholder="t('profile.fleetPlaceholder')" />
                <small>{{ t('profile.externalFleetHint') }}</small>
              </label>

              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.availability') }}</span>
                <input v-model="form.availability" maxlength="240" :placeholder="t('fleets.directory.availabilityPlaceholder')" />
              </label>

              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.timezone') }}</span>
                <input v-model="form.timezone" maxlength="80" :placeholder="t('fleets.directory.timezonePlaceholder')" />
              </label>

              <label class="input-panel embedded-field profile-field-wide">
                <span>{{ t('fleets.directory.discord') }}</span>
                <input v-model="form.discord_handle" maxlength="120" :placeholder="t('fleets.directory.discordPlaceholder')" />
              </label>

              <fieldset class="input-panel embedded-field profile-field-wide">
                <legend>{{ t('fleets.directory.preferredShips') }}</legend>
                <PreferenceTransferList v-model="form.preferred_ship_ids" :options="preferredShipOptions" />
              </fieldset>

              <fieldset class="input-panel embedded-field profile-field-wide">
                <legend>{{ t('fleets.directory.preferredRoles') }}</legend>
                <PreferenceTransferList v-model="form.preferred_role_ids" :options="preferredRoleOptions" />
              </fieldset>

              <label class="input-panel embedded-field profile-note-field profile-field-wide">
                <span>{{ t('profile.note') }}</span>
                <textarea v-model="form.note" maxlength="1000" rows="7" :placeholder="t('profile.notePlaceholder')"></textarea>
              </label>
            </div>

            <p v-if="error" class="error-text profile-message">{{ error }}</p>
            <p v-if="success" class="success-text profile-message">{{ success }}</p>

            <div class="profile-save-bar">
              <span class="muted">@{{ form.username }}</span>
              <button class="form-button primary-action" type="submit" :disabled="saving">
                {{ saving ? t('profile.saving') : t('profile.save') }}
              </button>
            </div>
          </form>

          <aside class="profile-side-stack profile-command-stack">
            <section class="wire-section profile-command-card profile-fleet-card">
              <div class="workspace-section-heading compact-heading">
                <div>
                  <p class="eyebrow">{{ t('profile.fleetMemberships.eyebrow') }}</p>
                  <h2>{{ t('profile.fleetMemberships.title') }}</h2>
                </div>
                <span v-if="hasOfficialFleetLink" class="summary-pill fleet-status-pill">{{ t(`fleets.status.${form.fleet_membership_status}`) }}</span>
              </div>

              <article v-if="hasOfficialFleetLink" class="profile-primary-fleet-row polished-membership-card">
                <div>
                  <strong>{{ form.fleet_name }}</strong>
                  <small v-if="primaryFleetMembership">{{ t(`fleets.focus.${primaryFleetMembership.fleet.focus}`) }}</small>
                  <small v-else>{{ t('profile.fleetMemberships.syncedHint') }}</small>
                </div>
                <span class="summary-pill">{{ t(`fleets.roles.${form.fleet_membership_role || 'member'}`) }}</span>
              </article>
              <p v-else class="muted">{{ t('profile.fleetMemberships.empty') }}</p>

              <div v-if="activeFleetMemberships.length > 1" class="profile-membership-list">
                <article v-for="membership in activeFleetMemberships" :key="membership.id" class="profile-membership-row">
                  <div><strong>{{ membership.fleet.name }}</strong><span>{{ t(`fleets.focus.${membership.fleet.focus}`) }}</span></div>
                  <span class="summary-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
                </article>
              </div>

              <div class="form-actions compact-actions">
                <RouterLink class="button-box" to="/fleet">{{ t('profile.fleetMemberships.browse') }}</RouterLink>
                <RouterLink v-if="leadershipMemberships.length" class="button-box primary-action" to="/fleets">{{ t('profile.fleetMemberships.manage') }}</RouterLink>
              </div>
            </section>

            <section class="wire-section profile-command-card profile-tools-card">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('common.personalArea') }}</p><h2>{{ t('common.modules') }}</h2></div>
              </div>
              <RouterLink class="profile-tool-link" to="/profile/builds"><span><AppIcon name="builds" :size="18" /></span><span><strong>{{ t('myBuilds.profileCardTitle') }}</strong><small>{{ t('myBuilds.profileCardText') }}</small></span><b>→</b></RouterLink>
              <RouterLink class="profile-tool-link" to="/profile/groups"><span><AppIcon name="groups" :size="18" /></span><span><strong>{{ t('myGroups.profileCardTitle') }}</strong><small>{{ t('myGroups.profileCardText') }}</small></span><b>→</b></RouterLink>
              <RouterLink class="profile-tool-link" to="/profile/squads"><span><AppIcon name="users" :size="18" /></span><span><strong>{{ t('mySquads.profileCardTitle') }}</strong><small>{{ t('mySquads.profileCardText') }}</small></span><b>→</b></RouterLink>
            </section>

            <section class="wire-section profile-command-card password-panel">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('profile.password.eyebrow') }}</p><h2>{{ t('profile.password.title') }}</h2><p>{{ t('profile.password.subtitle') }}</p></div>
              </div>

              <form class="password-form" @submit.prevent="submitPasswordChange">
                <label class="input-panel embedded-field"><span>{{ t('profile.password.current') }}</span><input v-model="passwordForm.current_password" type="password" autocomplete="current-password" required /></label>
                <div class="password-field-grid">
                  <label class="input-panel embedded-field"><span>{{ t('profile.password.new') }}</span><input v-model="passwordForm.new_password" type="password" autocomplete="new-password" required minlength="12" /></label>
                  <label class="input-panel embedded-field"><span>{{ t('profile.password.repeat') }}</span><input v-model="passwordForm.repeat_password" type="password" autocomplete="new-password" required minlength="12" /></label>
                </div>
                <p v-if="passwordError" class="error-text profile-message">{{ passwordError }}</p>
                <p v-if="passwordSuccess" class="success-text profile-message">{{ passwordSuccess }}</p>
                <button class="form-button" type="submit" :disabled="changingPassword">{{ changingPassword ? t('profile.password.saving') : t('profile.password.save') }}</button>
              </form>
            </section>
          </aside>
        </div>
      </template>
    </div>
  </section>
</template>
