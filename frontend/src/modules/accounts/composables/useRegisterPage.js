import { onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getPublicOfficialFleet } from '@/modules/fleet/api/fleet'

export function useRegisterPage() {
  const { t } = useLocale()
  const { register } = useSession()

  const username = ref('')
  const displayName = ref('')
  const password = ref('')
  const wantsFleetMembership = ref(false)
  const fleetApplicationNote = ref('')
  const officialFleet = ref(null)
  const fleetLoading = ref(false)
  const fleetError = ref('')
  const isSubmitting = ref(false)
  const error = ref('')
  const success = ref(false)
  const submittedRequest = ref(null)

  async function loadOfficialFleet() {
    fleetLoading.value = true
    fleetError.value = ''
    try {
      officialFleet.value = await getPublicOfficialFleet()
    } catch (err) {
      fleetError.value = err.message || t('auth.registerFleetLoadError')
      officialFleet.value = null
      wantsFleetMembership.value = false
    } finally {
      fleetLoading.value = false
    }
  }

  async function submitRegister() {
    isSubmitting.value = true
    error.value = ''
    success.value = false
    try {
      const applyToFleet = wantsFleetMembership.value && Boolean(officialFleet.value?.id)
      const response = await register({
        username: username.value,
        display_name: displayName.value,
        password: password.value,
        wants_fleet_membership: applyToFleet,
        fleet_id: applyToFleet ? officialFleet.value.id : null,
        fleet_application_note: applyToFleet ? fleetApplicationNote.value : null,
      })
      submittedRequest.value = response.request
      success.value = true
      username.value = ''
      displayName.value = ''
      password.value = ''
      wantsFleetMembership.value = false
      fleetApplicationNote.value = ''
    } catch (err) {
      error.value = err.message || t('auth.registerError')
    } finally {
      isSubmitting.value = false
    }
  }

  onMounted(loadOfficialFleet)

  return {
    t,
    register,
    username,
    displayName,
    password,
    wantsFleetMembership,
    fleetApplicationNote,
    officialFleet,
    fleetLoading,
    fleetError,
    isSubmitting,
    error,
    success,
    submittedRequest,
    loadOfficialFleet,
    submitRegister,
  }
}
