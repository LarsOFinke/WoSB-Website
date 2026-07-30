import { computed, reactive, ref } from 'vue'

import { createModerator, listUsers, updateUser } from '@/modules/admin/api/admin'
import { filterAdminUsers } from '@/modules/admin/domain/adminWorkspace'

export function useAdminUsers({ isAdmin, user, t }) {
  const users = ref([])
  const userSearch = ref('')
  const userRole = ref('')
  const userStatus = ref('')
  const userLoading = ref(false)
  const userError = ref('')
  const moderatorSuccess = ref('')
  const moderatorForm = reactive({ username: '', display_name: '', password: '' })

  const filteredUsers = computed(() => filterAdminUsers(users.value, {
    search: userSearch.value,
    role: userRole.value,
    status: userStatus.value,
  }))
  const userCountLabel = computed(() => filteredUsers.value.length === 1
    ? t('admin.users.summaryOne')
    : t('admin.users.summaryMany', { count: filteredUsers.value.length }))

  async function loadUsers() {
    if (!isAdmin.value) return
    userLoading.value = true
    userError.value = ''
    try {
      users.value = await listUsers()
    } catch (err) {
      userError.value = err.message || t('admin.users.loadError')
    } finally {
      userLoading.value = false
    }
  }

  async function submitModerator() {
    userError.value = ''
    moderatorSuccess.value = ''
    try {
      await createModerator({ ...moderatorForm })
      Object.assign(moderatorForm, { username: '', display_name: '', password: '' })
      moderatorSuccess.value = t('admin.users.moderatorCreated')
      await loadUsers()
    } catch (err) {
      userError.value = err.message || t('admin.users.createModeratorError')
    }
  }

  async function changeUserRole(row, event) {
    userError.value = ''
    try {
      await updateUser(row.id, { role: event.target.value })
      await loadUsers()
    } catch (err) {
      userError.value = err.message || t('admin.users.loadError')
    }
  }

  async function toggleUserActive(row) {
    userError.value = ''
    try {
      await updateUser(row.id, { is_active: !row.is_active })
      await loadUsers()
    } catch (err) {
      userError.value = err.message || t('admin.users.loadError')
    }
  }

  function canManageUser(row) {
    if (row.id === user.value?.id || row.is_bootstrap_admin) return false
    if (row.role === 'admin') return canGrantAdmin()
    return true
  }

  function canToggleUserActive(row) {
    return canManageUser(row) && row.role !== 'admin'
  }

  function canGrantAdmin() {
    return Boolean(user.value?.can_grant_admin)
  }

  function resetUserFilters() {
    userSearch.value = ''
    userRole.value = ''
    userStatus.value = ''
  }

  return {
    users, userSearch, userRole, userStatus, userLoading, userError,
    moderatorSuccess, moderatorForm, filteredUsers, userCountLabel,
    loadUsers, submitModerator, changeUserRole, toggleUserActive,
    canManageUser, canToggleUserActive, canGrantAdmin, resetUserFilters,
  }
}
