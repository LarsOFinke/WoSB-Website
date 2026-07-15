import { computed, onMounted, reactive, ref } from 'vue'
import { useLocale } from '@/locales'
import { changePassword } from '@/modules/accounts/api/auth'
import { getProfile, getProfilePreferenceOptions, updateProfile } from '@/modules/accounts/api/profile'
import {
  createPasswordForm,
  createProfileForm,
  hydrateProfileForm,
  PROFILE_FOCUS_OPTIONS,
  profileCompletion as calculateProfileCompletion,
  profileInitials,
  profileUpdatePayload,
} from '@/modules/accounts/domain/profileForm'
import { useSession } from '@/modules/accounts/session'
import { listMyFleetMemberships } from '@/modules/fleet/api/fleet'

export function useProfilePage() {
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
  const form = reactive(createProfileForm())
  const passwordForm = reactive(createPasswordForm())
  const focusOptions = PROFILE_FOCUS_OPTIONS

  const activeFleetMemberships = computed(() => fleetMemberships.value.filter((membership) => ['active', 'pending'].includes(membership.status)))
  const leadershipMemberships = computed(() => fleetMemberships.value.filter((membership) => membership.status === 'active' && ['fleet_admiral', 'fleet_lieutenant'].includes(membership.role)))
  const primaryFleetMembership = computed(() => form.fleet_membership_id
    ? fleetMemberships.value.find((membership) => membership.id === form.fleet_membership_id) || null
    : null)
  const hasOfficialFleetLink = computed(() => Boolean(form.fleet_id && form.fleet_membership_status))
  const displayInitials = computed(() => profileInitials(form))
  const preferredFocusLabel = computed(() => form.preferred_focus ? t(`focus.${form.preferred_focus}`) : t('profile.noPreferredFocus'))
  const preferredShipOptions = computed(() => preferenceOptions.ships.map((ship) => ({ id: ship.id, label: `${ship.name} · Rate ${ship.rate}` })))
  const preferredRoleOptions = computed(() => preferenceOptions.roles.map((role) => ({ id: role.id, label: role.label })))
  const fleetStatusLabel = computed(() => hasOfficialFleetLink.value ? t(`fleets.status.${form.fleet_membership_status}`) : t('profile.fleetMemberships.empty'))
  const profileCompletion = computed(() => calculateProfileCompletion(form, hasOfficialFleetLink.value))
  const profileCompletionHint = computed(() => profileCompletion.value === 100
    ? t('profile.completion.complete')
    : t('profile.completion.hint'))

  function fillForm(user) {
    hydrateProfileForm(form, user)
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
      const updated = await updateProfile(profileUpdatePayload(form, hasOfficialFleetLink.value))
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
      Object.assign(passwordForm, createPasswordForm())
      passwordSuccess.value = t('profile.password.changed')
    } catch (err) {
      passwordError.value = err.message || t('profile.password.changeError')
    } finally {
      changingPassword.value = false
    }
  }

  onMounted(loadProfile)

  return {
    t, setSessionUser, loading, saving, changingPassword, error, success,
    passwordError, passwordSuccess, fleetMemberships, preferenceOptions,
    activeFleetMemberships, leadershipMemberships, primaryFleetMembership,
    hasOfficialFleetLink, displayInitials, preferredFocusLabel, preferredShipOptions,
    preferredRoleOptions, fleetStatusLabel, profileCompletion, profileCompletionHint,
    focusOptions, form, passwordForm, fillForm, loadMemberships, loadProfile,
    saveProfile, submitPasswordChange,
  }
}
