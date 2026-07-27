import { computed, onMounted, reactive, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getPublicOfficialFleet, joinFleet, listMyFleetMemberships } from '@/modules/fleet/api/fleet'

export function useFleetPublicPage() {
  const { t } = useLocale()
  const { isAuthenticated } = useSession()
  const fleet = ref(null)
  const loading = ref(false)
  const error = ref('')
  const membership = ref(null)
  const applying = ref(false)
  const applicationError = ref('')
  const applicationSuccess = ref('')
  const application = reactive({
    note: '',
  })

  const leaderCount = computed(() => fleet.value?.leaders?.length || 0)
  const canApply = computed(() => isAuthenticated.value && (!membership.value || membership.value.status === 'inactive'))
  const hasMembership = computed(() => Boolean(membership.value && ['pending', 'active'].includes(membership.value.status)))

  async function loadFleet() {
    loading.value = true
    error.value = ''
    try {
      fleet.value = await getPublicOfficialFleet()
      if (isAuthenticated.value) {
        try {
          const memberships = await listMyFleetMemberships()
          membership.value = memberships.find((row) => row.fleet?.id === fleet.value.id) || memberships[0] || null
        } catch (membershipError) {
          applicationError.value = membershipError.message || t('fleets.application.statusError')
        }
      }
    } catch (err) {
      error.value = err.message || t('fleets.loadError')
    } finally {
      loading.value = false
    }
  }

  async function submitFleetApplication() {
    if (!fleet.value || !canApply.value) return
    applying.value = true
    applicationError.value = ''
    applicationSuccess.value = ''
    try {
      membership.value = await joinFleet({
        fleet_id: fleet.value.id,
        note: application.note.trim() || null,
      })
      applicationSuccess.value = t('fleets.application.submitted')
    } catch (err) {
      applicationError.value = err.message || t('fleets.application.submitError')
    } finally {
      applying.value = false
    }
  }

  onMounted(loadFleet)

  return {
    t,
    isAuthenticated,
    fleet,
    loading,
    error,
    membership,
    applying,
    applicationError,
    applicationSuccess,
    application,
    leaderCount,
    canApply,
    hasMembership,
    loadFleet,
    submitFleetApplication,
  }
}
