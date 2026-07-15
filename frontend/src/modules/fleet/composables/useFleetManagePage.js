import { computed, onMounted, reactive, ref } from 'vue'
import { useLocale } from '@/locales'
import {
  FLEET_MEMBER_STATUSES,
  createFleetRole,
  deleteFleetRole,
  getOfficialFleetManagementDetail,
  listFleetRoles,
  updateFleet,
  updateFleetMembership,
  updateFleetRole,
} from '@/modules/fleet/api/fleet'
import {
  filterFleetMemberships,
  hasFleetMemberPermission,
  membershipFieldPayload,
  membershipManagement,
} from '@/modules/fleet/domain/fleetMemberships'
import { useSession } from '@/modules/accounts/session'

const EMPTY_ROLE_FORM = Object.freeze({ code: '', label: '', rank: 10, is_leadership: false, can_manage_fleet: false, can_manage_members: false, is_active: true })

export function useFleetManagePage() {
  const { t } = useLocale()
  const { user } = useSession()
  const selectedFleet = ref(null)
  const fleetRoles = ref([])
  const activeTab = ref('profile')
  const loading = ref(false)
  const saving = ref(false)
  const roleSaving = ref(false)
  const error = ref('')
  const success = ref('')
  const memberSearch = ref('')
  const memberStatusFilter = ref('active')
  const memberRoleFilter = ref('')
  const form = reactive({ description: '', standing_orders: '' })
  const roleForm = reactive({ ...EMPTY_ROLE_FORM, id: null })

  const memberships = computed(() => selectedFleet.value?.memberships || [])
  const roleMap = computed(() => new Map(fleetRoles.value.map((role) => [role.code, role])))
  const activeRoleOptions = computed(() => fleetRoles.value.filter((role) => role.is_active))
  const pendingMembers = computed(() => memberships.value.filter((row) => row.status === 'pending'))
  const activeMembers = computed(() => memberships.value.filter((row) => row.status === 'active'))
  const inactiveMembers = computed(() => memberships.value.filter((row) => row.status === 'inactive'))
  const leadershipMembers = computed(() => memberships.value.filter((row) => row.status === 'active' && roleMap.value.get(row.role)?.is_leadership))
  const filteredMembers = computed(() => filterFleetMemberships(memberships.value, { search: memberSearch.value, status: memberStatusFilter.value, role: memberRoleFilter.value }))
  const activeDirectoryMembers = computed(() => filteredMembers.value.filter((membership) => membership.status === 'active'))
  const protectedMembers = computed(() => memberships.value.filter((membership) => membershipManagement(membership).protected))
  const currentMembership = computed(() => memberships.value.find((membership) => membership.user?.id === user.value?.id && membership.status === 'active'))
  const canManageRoles = computed(() => user.value?.role === 'admin' || currentMembership.value?.role === 'fleet_admiral')

  const tabs = computed(() => [
    { key: 'profile', label: t('fleets.manage.tabs.profile'), count: null },
    { key: 'requests', label: t('fleets.manage.tabs.requests'), count: pendingMembers.value.length },
    { key: 'members', label: t('fleets.manage.tabs.members'), count: activeMembers.value.length + inactiveMembers.value.length },
    { key: 'directory', label: t('fleets.manage.tabs.directory'), count: activeMembers.value.length },
    ...(canManageRoles.value ? [{ key: 'roles', label: t('fleets.manage.tabs.roles'), count: fleetRoles.value.length }] : []),
  ])

  function managementFor(membership) { return membershipManagement(membership) }
  function roleOptionsFor(membership) { return managementFor(membership).assignable_roles || [] }
  function roleLabel(code) { return roleMap.value.get(code)?.label || t(`fleets.roles.${code}`) }
  function protectionLabel(membership) {
    const reason = managementFor(membership).reason
    return reason ? t(`fleets.manage.protectionReasons.${reason}`) : ''
  }
  function hasAnyMemberPermission(membership) { return hasFleetMemberPermission(membership) }
  function syncForm() {
    form.description = selectedFleet.value?.description || ''
    form.standing_orders = selectedFleet.value?.standing_orders || ''
  }
  function resetRoleForm() { Object.assign(roleForm, { ...EMPTY_ROLE_FORM, id: null }) }
  function editRole(role) { Object.assign(roleForm, { ...role }) }

  async function loadFleetDetail() {
    loading.value = true
    error.value = ''
    try {
      selectedFleet.value = await getOfficialFleetManagementDetail()
      if (selectedFleet.value) {
        syncForm()
        fleetRoles.value = await listFleetRoles(selectedFleet.value.id, true)
      } else fleetRoles.value = []
    } catch (err) {
      error.value = err.message || t('fleets.manage.loadError')
    } finally { loading.value = false }
  }

  async function saveFleet() {
    if (!selectedFleet.value) return
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      await updateFleet(selectedFleet.value.id, { description: form.description, standing_orders: form.standing_orders })
      success.value = t('fleets.manage.saved')
      await loadFleetDetail()
    } catch (err) { error.value = err.message || t('fleets.manage.saveError') }
    finally { saving.value = false }
  }

  async function setMember(membership, payload) {
    error.value = ''
    success.value = ''
    try {
      await updateFleetMembership(selectedFleet.value.id, membership.id, payload)
      success.value = t('fleets.manage.memberSaved')
      await loadFleetDetail()
    } catch (err) { error.value = err.message || t('fleets.manage.memberError') }
  }

  async function saveRole() {
    if (!selectedFleet.value || !canManageRoles.value) return
    roleSaving.value = true
    error.value = ''
    success.value = ''
    const payload = {
      label: roleForm.label,
      rank: Number(roleForm.rank),
      is_leadership: roleForm.is_leadership,
      can_manage_fleet: roleForm.can_manage_fleet,
      can_manage_members: roleForm.can_manage_members,
    }
    try {
      if (roleForm.id) {
        payload.is_active = roleForm.is_active
        await updateFleetRole(selectedFleet.value.id, roleForm.id, payload)
      } else {
        payload.code = roleForm.code
        await createFleetRole(selectedFleet.value.id, payload)
      }
      success.value = t('fleets.manage.roles.saved')
      resetRoleForm()
      await loadFleetDetail()
      activeTab.value = 'roles'
    } catch (err) { error.value = err.message || t('fleets.manage.roles.error') }
    finally { roleSaving.value = false }
  }

  async function removeRole(role) {
    if (!selectedFleet.value || role.is_system || !window.confirm(t('fleets.manage.roles.confirmDelete', { role: role.label }))) return
    error.value = ''
    try {
      await deleteFleetRole(selectedFleet.value.id, role.id)
      success.value = t('fleets.manage.roles.deleted')
      if (roleForm.id === role.id) resetRoleForm()
      await loadFleetDetail()
      activeTab.value = 'roles'
    } catch (err) { error.value = err.message || t('fleets.manage.roles.error') }
  }

  function fieldPayload(field, event) { return membershipFieldPayload(field, event.target.value) }
  onMounted(loadFleetDetail)

  return {
    t, user, selectedFleet, fleetRoles, activeRoleOptions, canManageRoles, activeTab, loading, saving, roleSaving, error, success,
    memberSearch, memberStatusFilter, memberRoleFilter, form, roleForm, memberships, pendingMembers, activeMembers,
    inactiveMembers, leadershipMembers, tabs, filteredMembers, activeDirectoryMembers, protectedMembers, managementFor,
    roleOptionsFor, roleLabel, protectionLabel, hasAnyMemberPermission, syncForm, resetRoleForm, editRole,
    loadFleetDetail, saveFleet, setMember, saveRole, removeRole, fieldPayload, FLEET_MEMBER_STATUSES,
  }
}
