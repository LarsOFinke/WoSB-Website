import { computed, onMounted, reactive, ref } from 'vue'
import { useLocale } from '@/locales'
import { FLEET_MEMBER_STATUSES, FLEET_ROLES, getOfficialFleetManagementDetail, updateFleet, updateFleetMembership } from '@/modules/fleet/api/fleet'
import {
  filterFleetMemberships,
  hasFleetMemberPermission,
  isFleetLeadership,
  membershipFieldPayload,
  membershipManagement,
} from '@/modules/fleet/domain/fleetMemberships'
import { useSession } from '@/modules/accounts/session'

export function useFleetManagePage() {
  const { t } = useLocale()
  const { user } = useSession()
  const selectedFleet = ref(null)
  const activeTab = ref('profile')
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const success = ref('')
  const memberSearch = ref('')
  const memberStatusFilter = ref('active')
  const memberRoleFilter = ref('')
  const form = reactive({ description: '', standing_orders: '' })

  const memberships = computed(() => selectedFleet.value?.memberships || [])
  const pendingMembers = computed(() => memberships.value.filter((row) => row.status === 'pending'))
  const activeMembers = computed(() => memberships.value.filter((row) => row.status === 'active'))
  const inactiveMembers = computed(() => memberships.value.filter((row) => row.status === 'inactive'))
  const leadershipMembers = computed(() => memberships.value.filter(isFleetLeadership))
  const filteredMembers = computed(() => filterFleetMemberships(memberships.value, {
    search: memberSearch.value,
    status: memberStatusFilter.value,
    role: memberRoleFilter.value,
  }))
  const activeDirectoryMembers = computed(() => filteredMembers.value.filter((membership) => membership.status === 'active'))
  const protectedMembers = computed(() => memberships.value.filter((membership) => membershipManagement(membership).protected))

  const tabs = computed(() => [
    { key: 'profile', label: t('fleets.manage.tabs.profile'), count: null },
    { key: 'requests', label: t('fleets.manage.tabs.requests'), count: pendingMembers.value.length },
    { key: 'members', label: t('fleets.manage.tabs.members'), count: activeMembers.value.length + inactiveMembers.value.length },
    { key: 'directory', label: t('fleets.manage.tabs.directory'), count: activeMembers.value.length },
  ])

  function managementFor(membership) {
    return membershipManagement(membership)
  }

  function roleOptionsFor(membership) {
    return managementFor(membership).assignable_roles || []
  }

  function protectionLabel(membership) {
    const reason = managementFor(membership).reason
    return reason ? t(`fleets.manage.protectionReasons.${reason}`) : ''
  }

  function hasAnyMemberPermission(membership) {
    return hasFleetMemberPermission(membership)
  }

  function syncForm() {
    form.description = selectedFleet.value?.description || ''
    form.standing_orders = selectedFleet.value?.standing_orders || ''
  }

  async function loadFleetDetail() {
    loading.value = true
    error.value = ''
    try {
      selectedFleet.value = await getOfficialFleetManagementDetail()
      if (selectedFleet.value) syncForm()
    } catch (err) {
      error.value = err.message || t('fleets.manage.loadError')
    } finally {
      loading.value = false
    }
  }

  async function saveFleet() {
    if (!selectedFleet.value) return
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      await updateFleet(selectedFleet.value.id, {
        description: form.description,
        standing_orders: form.standing_orders,
      })
      success.value = t('fleets.manage.saved')
      await loadFleetDetail()
    } catch (err) {
      error.value = err.message || t('fleets.manage.saveError')
    } finally {
      saving.value = false
    }
  }

  async function setMember(membership, payload) {
    error.value = ''
    success.value = ''
    try {
      await updateFleetMembership(selectedFleet.value.id, membership.id, payload)
      success.value = t('fleets.manage.memberSaved')
      await loadFleetDetail()
    } catch (err) {
      error.value = err.message || t('fleets.manage.memberError')
    }
  }

  function fieldPayload(field, event) {
    return membershipFieldPayload(field, event.target.value)
  }

  onMounted(loadFleetDetail)

  return {
    t, user, selectedFleet, activeTab, loading, saving, error, success,
    memberSearch, memberStatusFilter, memberRoleFilter, form, memberships,
    pendingMembers, activeMembers, inactiveMembers, leadershipMembers, tabs,
    filteredMembers, activeDirectoryMembers, protectedMembers, managementFor,
    roleOptionsFor, protectionLabel, hasAnyMemberPermission, syncForm,
    loadFleetDetail, saveFleet, setMember, fieldPayload,
    FLEET_MEMBER_STATUSES, FLEET_ROLES,
  }
}
