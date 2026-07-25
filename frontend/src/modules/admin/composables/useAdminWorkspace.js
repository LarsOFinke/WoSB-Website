import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { useAdminBuilds } from '@/modules/admin/composables/useAdminBuilds'
import { useAdminCalendar } from '@/modules/admin/composables/useAdminCalendar'
import { useAdminContent } from '@/modules/admin/composables/useAdminContent'
import { useAdminLogs } from '@/modules/admin/composables/useAdminLogs'
import { useAdminOperations } from '@/modules/admin/composables/useAdminOperations'
import { useAdminRegistrations } from '@/modules/admin/composables/useAdminRegistrations'
import { useAdminUsers } from '@/modules/admin/composables/useAdminUsers'
import { crewTotal } from '@/modules/admin/domain/adminWorkspace'

const ADMIN_ONLY_TABS = new Set(['status', 'logs', 'ip-blocks', 'audit', 'users'])

export function useAdminWorkspace() {
  const route = useRoute()
  const router = useRouter()
  const { locale, t } = useLocale()
  const { isAdmin, isStaff, loadSession, sessionState, user } = useSession()
  const activeTab = ref('overview')
  const overviewLoading = ref(false)
  const pendingDelete = reactive({ type: '', id: null })

  function clearConfirmation() {
    pendingDelete.type = ''
    pendingDelete.id = null
  }

  function isPending(type, id) {
    return pendingDelete.type === type && pendingDelete.id === id
  }

  function askDelete(type, id) {
    pendingDelete.type = type
    pendingDelete.id = id
  }

  const buildsWorkspace = useAdminBuilds({ isStaff, t, clearConfirmation })
  const usersWorkspace = useAdminUsers({ isAdmin, user, t })
  const registrationsWorkspace = useAdminRegistrations({
    isStaff,
    t,
    loadUsers: usersWorkspace.loadUsers,
  })
  const calendarWorkspace = useAdminCalendar({ isStaff, locale, t, clearConfirmation })
  const contentWorkspace = useAdminContent({ isStaff, t, clearConfirmation })
  const logsWorkspace = useAdminLogs({ isAdmin, activeTab, t })
  const operationsWorkspace = useAdminOperations({
    isAdmin,
    activeTab,
    t,
    logs: logsWorkspace,
  })

  const tabGroups = computed(() => [
    {
      key: 'workspace',
      label: t('admin.workspace.navigation.workspace'),
      tabs: [
        { key: 'overview', icon: 'compass', label: t('admin.tabs.overview') },
        { key: 'registrations', icon: 'inbox', label: t('admin.tabs.registrations') },
        { key: 'calendar', icon: 'calendar', label: t('admin.tabs.calendar') },
        { key: 'content', icon: 'forum', label: t('admin.tabs.content') },
        { key: 'builds', icon: 'builds', label: t('admin.tabs.builds') },
      ],
    },
    {
      key: 'operations',
      label: t('admin.workspace.navigation.operations'),
      tabs: [
        { key: 'status', icon: 'activity', label: t('admin.tabs.status'), adminOnly: true },
        { key: 'logs', icon: 'activity', label: t('admin.tabs.logs'), adminOnly: true },
        { key: 'ip-blocks', icon: 'lock', label: t('admin.tabs.ipBlocks'), adminOnly: true },
        { key: 'audit', icon: 'inbox', label: t('admin.tabs.audit'), adminOnly: true },
      ],
    },
    {
      key: 'administration',
      label: t('admin.workspace.navigation.administration'),
      tabs: [
        { key: 'users', icon: 'users', label: t('admin.tabs.users'), adminOnly: true },
      ],
    },
  ].map((group) => ({
    ...group,
    tabs: group.tabs.filter((tab) => !tab.adminOnly || isAdmin.value),
  })).filter((group) => group.tabs.length))

  function canAccessTab(tab) {
    if (!isStaff.value) return false
    if (ADMIN_ONLY_TABS.has(tab)) return isAdmin.value
    return true
  }

  function navigateToTab(tab) {
    if (!canAccessTab(tab)) return
    activeTab.value = tab
    const query = tab === 'overview' ? {} : { section: tab }
    if (String(route.query.section || '') !== String(query.section || '')) {
      router.replace({ path: '/admin', query })
    }
  }

  async function loadOverview() {
    if (!isStaff.value) return
    overviewLoading.value = true
    const tasks = [
      registrationsWorkspace.loadRegistrations(),
      calendarWorkspace.loadCalendar(),
      contentWorkspace.loadContent(),
      buildsWorkspace.loadBuilds(),
    ]
    if (isAdmin.value) {
      tasks.push(
        operationsWorkspace.loadStatus(),
        usersWorkspace.loadUsers(),
        operationsWorkspace.loadAdminOverviewMetrics(),
      )
    }
    await Promise.allSettled(tasks)
    overviewLoading.value = false
  }

  watch(activeTab, async (tab) => {
    clearConfirmation()
    if (!canAccessTab(tab)) {
      activeTab.value = 'overview'
      return
    }
    if (tab === 'overview') await loadOverview()
    if (tab === 'builds') await buildsWorkspace.loadBuilds()
    if (tab === 'status') await Promise.all([
      operationsWorkspace.loadStatus(),
      operationsWorkspace.loadAdminOverviewMetrics(),
    ])
    if (tab === 'users') await usersWorkspace.loadUsers()
    if (tab === 'registrations') await registrationsWorkspace.loadRegistrations()
    if (tab === 'logs') await logsWorkspace.loadLogs()
    if (tab === 'calendar') await calendarWorkspace.loadCalendar()
    if (tab === 'content') await contentWorkspace.loadContent()
  })

  watch(() => route.query.section, (section) => {
    if (route.path !== '/admin') return
    const requestedTab = Array.isArray(section) ? section[0] : section
    const nextTab = requestedTab && canAccessTab(requestedTab) ? requestedTab : 'overview'
    if (activeTab.value !== nextTab) activeTab.value = nextTab
  })

  onMounted(async () => {
    if (!sessionState.isReady) await loadSession()
    const requestedTab = Array.isArray(route.query.section) ? route.query.section[0] : route.query.section
    activeTab.value = requestedTab && canAccessTab(requestedTab) ? requestedTab : 'overview'
    if (activeTab.value === 'overview') await loadOverview()
  })

  return {
    locale,
    t,
    isAdmin,
    isStaff,
    sessionState,
    user,
    activeTab,
    tabGroups,
    overviewLoading,
    pendingDelete,
    crewTotal,
    clearConfirmation,
    isPending,
    askDelete,
    navigateToTab,
    canAccessTab,
    loadOverview,
    ...buildsWorkspace,
    ...usersWorkspace,
    ...registrationsWorkspace,
    ...calendarWorkspace,
    ...contentWorkspace,
    ...logsWorkspace,
    ...operationsWorkspace,
  }
}
