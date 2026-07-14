<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import SystemOperationsPanel from '@/modules/admin/components/SystemOperationsPanel.vue'
import SecurityLogDashboard from '@/modules/admin/components/SecurityLogDashboard.vue'
import AuditLogPanel from '@/modules/admin/components/AuditLogPanel.vue'
import IpBlockManagementPanel from '@/modules/admin/components/IpBlockManagementPanel.vue'
import OutboundWebhookManagementPanel from '@/modules/admin/components/OutboundWebhookManagementPanel.vue'
import StaffOverviewPanel from '@/modules/admin/components/StaffOverviewPanel.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import {
  approveRegistrationRequest,
  createModerator,
  deleteAdminBuild,
  deleteAdminForumThread,
  deleteAdminGuide,
  getAdminLogSummary,
  getIpBlockSummary,
  getOutboundWebhookSummary,
  listAdminBuilds,
  listAdminForumThreads,
  listAdminGuides,
  listAdminLogs,
  listRegistrationRequests,
  listUsers,
  rejectRegistrationRequest,
  updateUser,
} from '@/modules/admin/api/admin'
import { closeGroup, listGroups } from '@/modules/groups/api/groups'
import { deleteFleetEvent, FLEET_EVENT_CATEGORIES, listFleetEvents } from '@/modules/calendar/api/calendar'
import { useSession } from '@/modules/accounts/session'

const { locale, t } = useLocale()
const { isAdmin, isStaff, loadSession, sessionState, user } = useSession()

const today = new Date()
const sevenDaysAgo = new Date(today)
sevenDaysAgo.setDate(today.getDate() - 6)
const ninetyDaysFromNow = new Date(today)
ninetyDaysFromNow.setDate(today.getDate() + 90)
const isoDate = (value) => value.toISOString().slice(0, 10)

const activeTab = ref('overview')
const ADMIN_ONLY_TABS = new Set(['status', 'logs', 'ip-blocks', 'audit', 'integrations', 'users'])
const builds = ref([])
const users = ref([])
const fleetEvents = ref([])
const forumThreads = ref([])
const guides = ref([])
const groups = ref([])
const registrationRequests = ref([])
const appLogs = ref([])
const ipBlockPrefill = ref('')
const logSummary = ref({ total: 0, errors: 0, warnings: 0, slow_requests: 0, recent_status: {} })
const ipBlockOverview = ref({ total: 0, active: 0, permanent: 0, temporary: 0, expired: 0, unblocked: 0 })
const webhookOverview = ref({ total: 0, active: 0, failing: 0, successful_deliveries: 0, failed_deliveries: 0 })
const overviewLoading = ref(false)
const search = ref('')
const contentSearch = ref('')
const calendarCategory = ref('')
const registrationStatus = ref('pending')
const registrationSearch = ref('')
const registrationFromDate = ref('')
const registrationToDate = ref('')
const calendarSearch = ref('')
const calendarFromDate = ref(isoDate(today))
const calendarToDate = ref(isoDate(ninetyDaysFromNow))
const contentScope = ref('all')
const contentOwner = ref('')
const buildType = ref('')
const buildRate = ref('')
const buildVisibility = ref('')
const userSearch = ref('')
const userRole = ref('')
const userStatus = ref('')
const logLevel = ref('')
const logPath = ref('')
const logIp = ref('')
const logThreat = ref('')
const logFromDate = ref(isoDate(sevenDaysAgo))
const logToDate = ref(isoDate(today))
const logSort = ref('created_at')
const logOrder = ref('desc')
const loading = ref(false)
const userLoading = ref(false)
const calendarLoading = ref(false)
const contentLoading = ref(false)
const registrationLoading = ref(false)
const logsLoading = ref(false)
const error = ref('')
const userError = ref('')
const calendarError = ref('')
const contentError = ref('')
const registrationError = ref('')
const logsError = ref('')
const moderatorSuccess = ref('')
const pendingDelete = reactive({ type: '', id: null })
const registrationDecisionNotes = reactive({})
const apiStatus = ref(t('admin.status.loading'))
const apiStatusDetail = ref(t('admin.status.loadingDetail'))
let searchTimer = null
let registrationSearchTimer = null
let contentTimer = null
let logFilterTimer = null

const moderatorForm = reactive({ username: '', display_name: '', password: '' })

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
      { key: 'integrations', icon: 'spark', label: t('admin.tabs.integrations'), adminOnly: true },
      { key: 'users', icon: 'users', label: t('admin.tabs.users'), adminOnly: true },
    ],
  },
].map((group) => ({
  ...group,
  tabs: group.tabs.filter((tab) => !tab.adminOnly || isAdmin.value),
})).filter((group) => group.tabs.length))

const filteredBuilds = computed(() => builds.value.filter((build) => {
  if (buildRate.value && String(build.ship?.rate || '') !== String(buildRate.value)) return false
  if (buildVisibility.value === 'official' && !build.is_official_template) return false
  if (buildVisibility.value === 'community' && build.is_official_template) return false
  return true
}))
const filteredUsers = computed(() => {
  const term = userSearch.value.trim().toLowerCase()
  return users.value.filter((row) => {
    if (term && !`${row.username} ${row.display_name}`.toLowerCase().includes(term)) return false
    if (userRole.value && row.role !== userRole.value) return false
    if (userStatus.value === 'active' && !row.is_active) return false
    if (userStatus.value === 'inactive' && row.is_active) return false
    return true
  })
})
const filteredEvents = computed(() => {
  const term = calendarSearch.value.trim().toLowerCase()
  return [...fleetEvents.value]
    .filter((event) => !term || `${event.title} ${event.location || ''} ${event.description || ''}`.toLowerCase().includes(term))
    .sort((a, b) => new Date(a.start_at) - new Date(b.start_at))
})
const upcomingEvents = computed(() => filteredEvents.value.slice(0, 40))
const contentOwnerTerm = computed(() => contentOwner.value.trim().toLowerCase())
function ownerMatches(row) {
  if (!contentOwnerTerm.value) return true
  return `${row.owner?.display_name || ''} ${row.owner?.username || ''}`.toLowerCase().includes(contentOwnerTerm.value)
}
const visibleForumThreads = computed(() => forumThreads.value.filter(ownerMatches))
const visibleGuides = computed(() => guides.value.filter(ownerMatches))
const visibleGroups = computed(() => groups.value.filter(ownerMatches))
const visibleContentCount = computed(() => {
  if (contentScope.value === 'forum') return visibleForumThreads.value.length
  if (contentScope.value === 'guides') return visibleGuides.value.length
  if (contentScope.value === 'groups') return visibleGroups.value.length
  return visibleForumThreads.value.length + visibleGuides.value.length + visibleGroups.value.length
})
const pendingRegistrationRows = computed(() => registrationRequests.value.filter((row) => row.status === 'pending'))
const oldestPendingRequest = computed(() => [...pendingRegistrationRows.value].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))[0] || null)
const nextOverviewEvent = computed(() => filteredEvents.value.find((event) => new Date(event.end_at || event.start_at) >= new Date()) || null)
const buildRates = computed(() => [...new Set(builds.value.map((build) => build.ship?.rate).filter((rate) => rate !== null && rate !== undefined))].sort((a, b) => Number(a) - Number(b)))
const buildCountLabel = computed(() => filteredBuilds.value.length === 1 ? t('admin.builds.summaryOne') : t('admin.builds.summaryMany', { count: filteredBuilds.value.length }))
const userCountLabel = computed(() => filteredUsers.value.length === 1 ? t('admin.users.summaryOne') : t('admin.users.summaryMany', { count: filteredUsers.value.length }))
const eventCountLabel = computed(() => upcomingEvents.value.length === 1 ? t('admin.calendar.summaryOne') : t('admin.calendar.summaryMany', { count: upcomingEvents.value.length }))
const contentCountLabel = computed(() => t('admin.content.summary', { count: visibleContentCount.value }))
const registrationCountLabel = computed(() => registrationRequests.value.length === 1 ? t('admin.registrations.summaryOne') : t('admin.registrations.summaryMany', { count: registrationRequests.value.length }))
const logsCountLabel = computed(() => t('admin.logs.summary', { count: logSummary.value.total || appLogs.value.length }))
const categoryOptions = computed(() => [{ value: '', label: t('calendar.categories.all') }, ...FLEET_EVENT_CATEGORIES.map((value) => ({ value, label: t(`calendar.categories.${value}`) }))])
function crewTotal(build) {
  return build.sailors + build.soldiers + build.musketeers + build.mercenaries
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatEventRange(event) {
  if (event.all_day) return `${new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(event.start_at))} · ${t('calendar.list.allDay')}`
  return `${formatDateTime(event.start_at)} – ${new Intl.DateTimeFormat(locale.value, { timeStyle: 'short' }).format(new Date(event.end_at))}`
}

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

async function loadBuilds() {
  if (!isStaff.value) return
  loading.value = true
  error.value = ''
  try {
    builds.value = await listAdminBuilds(search.value, buildType.value)
  } catch (err) {
    error.value = err.message || t('admin.builds.loadError')
  } finally {
    loading.value = false
  }
}

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

async function loadStatus() {
  if (!isAdmin.value) return
  apiStatus.value = t('admin.status.loading')
  apiStatusDetail.value = t('admin.status.loadingDetail')
  try {
    const response = await fetch('/api/health')
    if (!response.ok) throw new Error(`API responded with ${response.status}`)
    const payload = await response.json()
    apiStatus.value = t('admin.status.online')
    apiStatusDetail.value = payload.status ? t('admin.status.detailWithStatus', { status: payload.status }) : t('admin.status.onlineDetail')
  } catch {
    apiStatus.value = t('admin.status.offline')
    apiStatusDetail.value = t('admin.status.offlineDetail')
  }
}

async function loadAdminOverviewMetrics() {
  if (!isAdmin.value) return
  try {
    const [logs, blocks, webhooks] = await Promise.all([
      getAdminLogSummary({ fromDate: logFromDate.value, toDate: logToDate.value }),
      getIpBlockSummary(),
      getOutboundWebhookSummary(),
    ])
    logSummary.value = logs
    ipBlockOverview.value = blocks
    webhookOverview.value = webhooks
  } catch (err) {
    logsError.value = err.message || t('admin.workspace.overviewLoadError')
  }
}

async function loadOverview() {
  if (!isStaff.value) return
  overviewLoading.value = true
  const tasks = [loadRegistrations(), loadCalendar(), loadContent(), loadBuilds()]
  if (isAdmin.value) tasks.push(loadStatus(), loadUsers(), loadAdminOverviewMetrics())
  await Promise.allSettled(tasks)
  overviewLoading.value = false
}

async function loadRegistrations() {
  if (!isStaff.value) return
  registrationLoading.value = true
  registrationError.value = ''
  try {
    registrationRequests.value = await listRegistrationRequests({
      status: registrationStatus.value,
      search: registrationSearch.value,
      fromDate: registrationFromDate.value,
      toDate: registrationToDate.value,
    })
  } catch (err) {
    registrationError.value = err.message || t('admin.registrations.loadError')
  } finally {
    registrationLoading.value = false
  }
}

async function approveRegistration(id) {
  registrationError.value = ''
  try {
    await approveRegistrationRequest(id, registrationDecisionNotes[id] || '')
    delete registrationDecisionNotes[id]
    await Promise.all([loadRegistrations(), loadUsers()])
  } catch (err) {
    registrationError.value = err.message || t('admin.registrations.approveError')
  }
}

async function rejectRegistration(id) {
  registrationError.value = ''
  try {
    await rejectRegistrationRequest(id, registrationDecisionNotes[id] || '')
    delete registrationDecisionNotes[id]
    await loadRegistrations()
  } catch (err) {
    registrationError.value = err.message || t('admin.registrations.rejectError')
  }
}

async function loadLogs() {
  if (!isAdmin.value) return
  logsLoading.value = true
  logsError.value = ''
  try {
    const [summary, rows] = await Promise.all([
      getAdminLogSummary({ level: logLevel.value, path: logPath.value, clientIp: logIp.value, threatLevel: logThreat.value, fromDate: logFromDate.value, toDate: logToDate.value }),
      listAdminLogs({ level: logLevel.value, path: logPath.value, clientIp: logIp.value, threatLevel: logThreat.value, fromDate: logFromDate.value, toDate: logToDate.value, sort: logSort.value, order: logOrder.value, limit: 140 }),
    ])
    logSummary.value = summary
    appLogs.value = rows
  } catch (err) {
    logsError.value = err.message || t('admin.logs.loadError')
  } finally {
    logsLoading.value = false
  }
}

function formatDuration(value) {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value)} ms`
}

function openIpBlockManager(ipAddress) {
  if (!isAdmin.value) return
  ipBlockPrefill.value = ipAddress || ''
  activeTab.value = 'ip-blocks'
}

function openLogsForIp(ipAddress) {
  if (!isAdmin.value) return
  logIp.value = ipAddress || ''
  activeTab.value = 'logs'
}

async function loadCalendar() {
  if (!isStaff.value) return
  calendarLoading.value = true
  calendarError.value = ''
  const start = calendarFromDate.value ? new Date(`${calendarFromDate.value}T00:00:00`) : new Date()
  start.setHours(0, 0, 0, 0)
  const end = calendarToDate.value ? new Date(`${calendarToDate.value}T23:59:59`) : new Date(start)
  if (!calendarToDate.value) end.setDate(end.getDate() + 90)
  try {
    fleetEvents.value = await listFleetEvents({ start: start.toISOString(), end: end.toISOString(), category: calendarCategory.value })
  } catch (err) {
    calendarError.value = err.message || t('admin.calendar.loadError')
  } finally {
    calendarLoading.value = false
  }
}

async function loadContent() {
  if (!isStaff.value) return
  contentLoading.value = true
  contentError.value = ''
  try {
    const [threadRows, guideRows, groupRows] = await Promise.all([
      listAdminForumThreads(contentSearch.value),
      listAdminGuides(contentSearch.value),
      listGroups({ search: contentSearch.value }),
    ])
    forumThreads.value = threadRows
    guides.value = guideRows
    groups.value = groupRows
  } catch (err) {
    contentError.value = err.message || t('admin.content.loadError')
  } finally {
    contentLoading.value = false
  }
}

async function confirmDeleteBuild(buildId) {
  error.value = ''
  try {
    await deleteAdminBuild(buildId)
    clearConfirmation()
    await loadBuilds()
  } catch (err) {
    error.value = err.message || t('admin.builds.deleteError')
  }
}

async function confirmDeleteEvent(eventId) {
  calendarError.value = ''
  try {
    await deleteFleetEvent(eventId)
    clearConfirmation()
    await loadCalendar()
  } catch (err) {
    calendarError.value = err.message || t('admin.calendar.deleteError')
  }
}

async function confirmDeleteThread(threadId) {
  contentError.value = ''
  try {
    await deleteAdminForumThread(threadId)
    clearConfirmation()
    await loadContent()
  } catch (err) {
    contentError.value = err.message || t('admin.content.deleteError')
  }
}

async function confirmDeleteGuide(guideId) {
  contentError.value = ''
  try {
    await deleteAdminGuide(guideId)
    clearConfirmation()
    await loadContent()
  } catch (err) {
    contentError.value = err.message || t('admin.content.deleteError')
  }
}

async function confirmCloseGroup(groupId) {
  contentError.value = ''
  try {
    await closeGroup(groupId)
    clearConfirmation()
    await loadContent()
  } catch (err) {
    contentError.value = err.message || t('admin.content.closeError')
  }
}

async function submitModerator() {
  userError.value = ''
  moderatorSuccess.value = ''
  try {
    await createModerator({ ...moderatorForm })
    moderatorForm.username = ''
    moderatorForm.display_name = ''
    moderatorForm.password = ''
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
  return row.id !== user.value?.id && row.role !== 'admin'
}

function navigateToTab(tab) {
  if (canAccessTab(tab)) activeTab.value = tab
}

function resetRegistrationFilters() {
  registrationStatus.value = 'pending'
  registrationSearch.value = ''
  registrationFromDate.value = ''
  registrationToDate.value = ''
}

function resetCalendarFilters() {
  calendarCategory.value = ''
  calendarSearch.value = ''
  calendarFromDate.value = isoDate(today)
  calendarToDate.value = isoDate(ninetyDaysFromNow)
}

function resetContentFilters() {
  contentSearch.value = ''
  contentScope.value = 'all'
  contentOwner.value = ''
}

function resetBuildFilters() {
  search.value = ''
  buildType.value = ''
  buildRate.value = ''
  buildVisibility.value = ''
}

function resetUserFilters() {
  userSearch.value = ''
  userRole.value = ''
  userStatus.value = ''
}

watch([search, buildType], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

watch(registrationSearch, () => {
  window.clearTimeout(registrationSearchTimer)
  registrationSearchTimer = window.setTimeout(loadRegistrations, 240)
})

watch(contentSearch, () => {
  window.clearTimeout(contentTimer)
  contentTimer = window.setTimeout(loadContent, 220)
})

watch([calendarCategory, calendarFromDate, calendarToDate], loadCalendar)
watch([registrationStatus, registrationFromDate, registrationToDate], loadRegistrations)
watch([logLevel, logIp, logThreat, logFromDate, logToDate, logSort, logOrder], loadLogs)
watch(logPath, () => {
  window.clearTimeout(logFilterTimer)
  logFilterTimer = window.setTimeout(loadLogs, 260)
})

function canAccessTab(tab) {
  if (!isStaff.value) return false
  if (ADMIN_ONLY_TABS.has(tab)) return isAdmin.value
  return true
}

watch(activeTab, async (tab) => {
  clearConfirmation()
  if (!canAccessTab(tab)) {
    activeTab.value = 'overview'
    return
  }
  if (tab === 'overview') await loadOverview()
  if (tab === 'builds') await loadBuilds()
  if (tab === 'status') await Promise.all([loadStatus(), loadAdminOverviewMetrics()])
  if (tab === 'users') await loadUsers()
  if (tab === 'registrations') await loadRegistrations()
  if (tab === 'logs') await loadLogs()
  if (tab === 'calendar') await loadCalendar()
  if (tab === 'content') await loadContent()
})

onMounted(async () => {
  if (!sessionState.isReady) await loadSession()
  activeTab.value = 'overview'
  await loadOverview()
})

onUnmounted(() => {
  window.clearTimeout(searchTimer)
  window.clearTimeout(registrationSearchTimer)
  window.clearTimeout(contentTimer)
  window.clearTimeout(logFilterTimer)
})
</script>

<template>
  <section class="admin-page" aria-labelledby="admin-title">
    <div class="wire-frame page-frame admin-frame staff-workspace-frame">
      <PageHeader
        :eyebrow="t('admin.eyebrow')"
        :title="isAdmin ? t('admin.title') : t('admin.moderatorTitle')"
        :description="isAdmin ? t('admin.subtitle') : t('admin.moderatorSubtitle')"
        title-id="admin-title"
      >
        <template #meta>
          <span v-if="user" class="summary-pill">{{ user.display_name }}</span>
          <span v-if="user" class="summary-pill">{{ t(`roles.${user.role}`) }}</span>
          <span v-if="isAdmin" class="summary-pill" :class="{ 'fleet-status-pill': apiStatus === t('admin.status.online') }">{{ apiStatus }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/calendar">{{ t('common.calendar') }}</RouterLink>
          <RouterLink v-if="isStaff" class="button-box primary-action" to="/calendar/new">{{ t('admin.quickActions.newEvent') }}</RouterLink>
        </template>
      </PageHeader>

      <section v-if="!isStaff" class="wire-section admin-locked">
        <h2>{{ t('admin.lockedTitle') }}</h2>
        <p>{{ t('admin.lockedText') }}</p>
        <RouterLink class="button-box primary-action" to="/login">{{ t('auth.login') }}</RouterLink>
      </section>

      <template v-else>
        <section class="wire-section staff-command-center polished-command-center" :aria-label="t('admin.quickActions.label')">
          <RouterLink class="staff-command-card" to="/calendar/new">
            <span class="staff-command-card-topline"><AppIcon name="calendar" :size="18" />{{ t('admin.quickActions.scheduleLabel') }}</span>
            <strong>{{ t('admin.quickActions.newEvent') }}</strong>
            <small>{{ t('admin.quickActions.scheduleText') }}</small>
            <AppIcon class="staff-command-card-arrow" name="arrow-right" :size="17" />
          </RouterLink>
          <RouterLink class="staff-command-card" to="/forum/new">
            <span class="staff-command-card-topline"><AppIcon name="forum" :size="18" />{{ t('admin.quickActions.forumLabel') }}</span>
            <strong>{{ t('admin.quickActions.newThread') }}</strong>
            <small>{{ t('admin.quickActions.forumText') }}</small>
            <AppIcon class="staff-command-card-arrow" name="arrow-right" :size="17" />
          </RouterLink>
          <RouterLink class="staff-command-card" to="/guides/new">
            <span class="staff-command-card-topline"><AppIcon name="guides" :size="18" />{{ t('admin.quickActions.guidesLabel') }}</span>
            <strong>{{ t('admin.quickActions.newGuide') }}</strong>
            <small>{{ t('admin.quickActions.guidesText') }}</small>
            <AppIcon class="staff-command-card-arrow" name="arrow-right" :size="17" />
          </RouterLink>
          <RouterLink v-if="isAdmin" class="staff-command-card" to="/admin/master-data">
            <span class="staff-command-card-topline"><AppIcon name="builds" :size="18" />{{ t('masterData.eyebrow') }}</span>
            <strong>{{ t('masterData.title') }}</strong>
            <small>{{ t('masterData.subtitle') }}</small>
            <AppIcon class="staff-command-card-arrow" name="arrow-right" :size="17" />
          </RouterLink>
          <RouterLink class="staff-command-card" to="/fleets">
            <span class="staff-command-card-topline"><AppIcon name="fleet" :size="18" />{{ t('fleets.manage.eyebrow') }}</span>
            <strong>{{ t('common.fleetManagement') }}</strong>
            <small>{{ t('fleets.manage.subtitle') }}</small>
            <AppIcon class="staff-command-card-arrow" name="arrow-right" :size="17" />
          </RouterLink>
        </section>

        <nav class="wire-section admin-tabs staff-tabs workspace-tab-rail" :aria-label="t('admin.tabsLabel')">
          <section v-for="group in tabGroups" :key="group.key" class="staff-tab-group">
            <span class="staff-tab-group-label">{{ group.label }}</span>
            <button
              v-for="tab in group.tabs"
              :key="tab.key"
              class="tab-button"
              :class="{ 'is-active': activeTab === tab.key }"
              type="button"
              :aria-current="activeTab === tab.key ? 'page' : undefined"
              @click="navigateToTab(tab.key)"
            >
              <span><AppIcon :name="tab.icon" :size="17" />{{ tab.label }}</span>
              <AppIcon name="chevron-right" :size="15" />
            </button>
          </section>
        </nav>

        <section v-if="activeTab === 'overview'" class="wire-section admin-panel staff-overview-shell">
          <StaffOverviewPanel
            :is-admin="isAdmin"
            :loading="overviewLoading"
            :pending-registrations="pendingRegistrationRows.length"
            :upcoming-events="filteredEvents.length"
            :content-items="forumThreads.length + guides.length + groups.length"
            :builds="builds.length"
            :users="users.length"
            :log-summary="logSummary"
            :ip-block-summary="ipBlockOverview"
            :webhook-summary="webhookOverview"
            :next-event="nextOverviewEvent"
            :oldest-pending-request="oldestPendingRequest"
            @navigate="navigateToTab"
            @refresh="loadOverview"
          />
        </section>

        <section v-if="activeTab === 'status' && isAdmin" class="wire-section admin-panel admin-status-panel">
          <SystemOperationsPanel :api-status="apiStatus" :api-status-detail="apiStatusDetail" :is-admin="isAdmin" @refresh-api="loadStatus" />

          <div class="workspace-metric-grid admin-dashboard-grid">
            <MetricCard :label="t('admin.registrations.dashboardLabel')" :value="pendingRegistrationRows.length" :hint="t('admin.registrations.dashboardHint')" tone="accent" />
            <MetricCard :label="t('admin.logs.total')" :value="logSummary.total" :hint="t('admin.logs.dashboardHint')" />
            <MetricCard :label="t('admin.logs.errors')" :value="logSummary.errors" :hint="t('admin.logs.errorHint')" tone="danger" />
            <MetricCard :label="t('admin.logs.slowRequests')" :value="logSummary.slow_requests" :hint="t('admin.logs.slowHint')" />
            <MetricCard :label="t('admin.workspace.cards.ipBlocks')" :value="ipBlockOverview.active" :hint="t('admin.workspace.cards.ipBlocksHint')" />
            <MetricCard :label="t('admin.workspace.cards.integrations')" :value="webhookOverview.active" :hint="t('admin.workspace.cards.integrationsHint', { failing: webhookOverview.failing })" :tone="webhookOverview.failing ? 'danger' : ''" />
          </div>
        </section>

        <section v-if="activeTab === 'registrations' && isStaff" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading">
            <div><h2>{{ t('admin.registrations.title') }}</h2><p>{{ t('admin.registrations.subtitle') }}</p></div>
            <span class="summary-pill">{{ registrationCountLabel }}</span>
          </div>
          <div class="staff-filter-surface">
            <div class="staff-filter-surface-head">
              <div><strong>{{ t('admin.workspace.filters.title') }}</strong><small>{{ t('admin.workspace.filters.registrationHint') }}</small></div>
              <button class="small-action" type="button" @click="resetRegistrationFilters">{{ t('admin.workspace.filters.reset') }}</button>
            </div>
            <div class="staff-filter-row staff-filter-row--wide">
              <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="registrationStatus"><option value="pending">{{ t('admin.registrations.status.pending') }}</option><option value="approved">{{ t('admin.registrations.status.approved') }}</option><option value="rejected">{{ t('admin.registrations.status.rejected') }}</option><option value="">{{ t('admin.registrations.status.all') }}</option></select></label>
              <label class="filter-box admin-search"><input v-model="registrationSearch" type="search" :placeholder="t('admin.workspace.filters.registrationSearch')" /></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.from') }}</span><input v-model="registrationFromDate" type="date" /></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.to') }}</span><input v-model="registrationToDate" type="date" /></label>
            </div>
          </div>
          <p v-if="registrationLoading" class="muted table-state">{{ t('admin.registrations.loading') }}</p>
          <p v-else-if="registrationError" class="error-text table-state">{{ registrationError }}</p>
          <p v-else-if="registrationRequests.length === 0" class="muted table-state">{{ t('admin.registrations.empty') }}</p>
          <div v-else class="admin-build-list registration-review-list">
            <article v-for="request in registrationRequests" :key="request.id" class="admin-build-row registration-review-row">
              <div class="admin-build-main">
                <strong>{{ request.display_name }}</strong>
                <span>{{ request.username }} · {{ formatDateTime(request.created_at) }} · {{ t(`admin.registrations.status.${request.status}`) }}</span>
                <small v-if="request.reviewed_at" class="muted">{{ t('admin.workspace.reviewedBy', { user: request.reviewed_by?.display_name || request.reviewed_by?.username || '—', date: formatDateTime(request.reviewed_at) }) }}</small>
                <p v-if="request.decision_note" class="muted">{{ t('admin.registrations.decisionNote') }}: {{ request.decision_note }}</p>
              </div>
              <div v-if="request.status === 'pending'" class="registration-actions">
                <label class="input-panel embedded-field"><span>{{ t('admin.registrations.noteLabel') }}</span><input v-model="registrationDecisionNotes[request.id]" maxlength="1000" :placeholder="t('admin.registrations.notePlaceholder')" /></label>
                <div class="hero-actions"><button class="form-button primary-action" type="button" @click="approveRegistration(request.id)">{{ t('admin.registrations.approve') }}</button><button class="danger-action" type="button" @click="rejectRegistration(request.id)">{{ t('admin.registrations.reject') }}</button></div>
              </div>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'logs' && isAdmin" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.logs.title') }}</h2><p>{{ t('admin.logs.subtitle') }}</p></div><div class="hero-actions"><span class="summary-pill">{{ logsCountLabel }}</span><button class="small-action" type="button" :disabled="logsLoading" @click="loadLogs">{{ t('admin.logs.refresh') }}</button></div></div>
          <div class="staff-log-workspace">
            <SecurityLogDashboard
              v-model:from-date="logFromDate"
              v-model:to-date="logToDate"
              v-model:threat-level="logThreat"
              v-model:selected-ip="logIp"
              :can-block="isAdmin"
              @block-ip="openIpBlockManager"
            />

            <article class="staff-log-surface log-filter-surface">
              <div class="staff-log-surface-head">
                <div>
                  <h3>{{ t('admin.logs.requestFilters') }}</h3>
                  <p>{{ t('admin.logs.requestFiltersHint') }}</p>
                </div>
                <span class="summary-pill">{{ t('admin.logs.total') }} · {{ logSummary.total }}</span>
              </div>
              <p class="muted log-storage-note">{{ t('logs.dbOnly') }}</p>
              <div class="staff-filter-row log-filter-row refined-log-filter-row">
                <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="logLevel"><option value="">{{ t('admin.logs.levelAll') }}</option><option>INFO</option><option>WARNING</option><option>ERROR</option><option>CRITICAL</option></select></label>
                <label class="filter-box admin-search"><input v-model="logPath" type="search" :placeholder="t('admin.logs.pathPlaceholder')" /></label>
                <label class="filter-box select-shell"><select v-model="logSort"><option value="created_at">{{ t('admin.logs.sortDate') }}</option><option value="ip">{{ t('admin.logs.sortIp') }}</option><option value="status">{{ t('admin.logs.sortStatus') }}</option><option value="duration">{{ t('admin.logs.sortDuration') }}</option><option value="level">{{ t('admin.logs.sortLevel') }}</option></select></label>
                <label class="filter-box select-shell"><select v-model="logOrder"><option value="desc">{{ t('admin.logs.desc') }}</option><option value="asc">{{ t('admin.logs.asc') }}</option></select></label>
              </div>
            </article>

            <article class="staff-log-surface log-table-surface">
              <div class="staff-log-surface-head">
                <div>
                  <h3>{{ t('admin.logs.resultsTitle') }}</h3>
                  <p>{{ t('admin.logs.resultsHint') }}</p>
                </div>
                <div class="admin-dashboard-grid log-summary-grid compact-log-summary-grid">
                  <article class="home-status-card refined-status-card"><span>{{ t('admin.logs.warnings') }}</span><strong>{{ logSummary.warnings }}</strong></article>
                  <article class="home-status-card refined-status-card"><span>{{ t('admin.logs.errors') }}</span><strong>{{ logSummary.errors }}</strong></article>
                  <article class="home-status-card refined-status-card"><span>{{ t('admin.logs.slowRequests') }}</span><strong>{{ logSummary.slow_requests }}</strong></article>
                </div>
              </div>

              <div class="staff-log-active-scope" aria-live="polite">
                <span>{{ t('admin.logs.activeScope') }}</span>
                <strong>{{ logFromDate }} – {{ logToDate }}</strong>
                <strong>{{ logThreat ? t(`admin.security.levels.${logThreat}`) : t('admin.security.allThreats') }}</strong>
                <strong>{{ logIp || t('admin.security.allIps') }}</strong>
                <strong v-if="logLevel">{{ logLevel }}</strong>
                <strong v-if="logPath">{{ logPath }}</strong>
              </div>

              <p v-if="logsLoading" class="muted table-state">{{ t('admin.logs.loading') }}</p>
              <p v-else-if="logsError" class="error-text table-state">{{ logsError }}</p>
              <p v-else-if="appLogs.length === 0" class="muted table-state">{{ t('admin.logs.empty') }}</p>
              <div v-else class="responsive-table-shell staff-log-table-shell">
                <table class="security-table staff-log-table">
                  <thead>
                    <tr>
                      <th>{{ t('admin.logs.sortDate') }}</th>
                      <th>{{ t('admin.logs.sortLevel') }}</th>
                      <th>Request</th>
                      <th>{{ t('logs.clientIp') }}</th>
                      <th>{{ t('admin.logs.sortStatus') }}</th>
                      <th>{{ t('admin.logs.sortDuration') }}</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="entry in appLogs" :key="entry.id">
                      <td>
                        <div class="staff-log-primary-cell">
                          <strong class="staff-log-timestamp">{{ formatDateTime(entry.created_at) }}</strong>
                          <small v-if="entry.request_id" class="staff-log-request-id" :title="entry.request_id">{{ t('admin.logs.requestId') }}: {{ entry.request_id }}</small>
                        </div>
                      </td>
                      <td><span class="staff-log-level-badge" :class="`level-${(entry.level || '').toLowerCase()}`">{{ entry.level }}</span></td>
                      <td>
                        <div class="staff-log-primary-cell">
                          <strong>{{ entry.method || entry.logger }}</strong>
                          <small class="staff-log-path" :title="entry.path || entry.message">{{ entry.path || entry.message }}</small>
                        </div>
                      </td>
                      <td>
                        <div class="staff-log-primary-cell">
                          <strong class="staff-log-ip" :title="entry.client_ip || '—'">{{ entry.client_ip || '—' }}</strong>
                          <small v-if="entry.user_agent" class="staff-log-user-agent" :title="entry.user_agent">{{ entry.user_agent }}</small>
                        </div>
                      </td>
                      <td>{{ entry.status_code || '—' }}</td>
                      <td>{{ formatDuration(entry.duration_ms) }}</td>
                      <td>
                        <div class="staff-log-primary-cell">
                          <small v-if="entry.query_string" class="staff-log-detail" :title="entry.query_string">{{ t('logs.queryString') }}: {{ entry.query_string }}</small>
                          <small v-if="entry.exception" class="error-text staff-log-detail" :title="entry.exception">{{ entry.exception }}</small>
                          <small v-if="!entry.query_string && !entry.exception">—</small>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'ip-blocks' && isAdmin" class="wire-section admin-panel staff-management-panel ip-block-admin-panel">
          <IpBlockManagementPanel
            :initial-ip="ipBlockPrefill"
            :can-manage="isAdmin"
            @consumed-initial-ip="ipBlockPrefill = ''"
            @view-logs="openLogsForIp"
          />
        </section>

        <section v-if="activeTab === 'audit' && isAdmin" class="wire-section admin-panel staff-management-panel">
          <AuditLogPanel />
        </section>

        <section v-if="activeTab === 'integrations' && isAdmin" class="wire-section admin-panel staff-management-panel">
          <div class="integration-context-grid">
            <article>
              <span class="command-deck-eyebrow">{{ t('admin.webhooks.eyebrow') }}</span>
              <strong>{{ webhookOverview.active }} / {{ webhookOverview.total }}</strong>
              <p>{{ t('admin.webhooks.subtitle') }}</p>
              <small v-if="webhookOverview.failing" class="error-text">{{ t('admin.workspace.cards.integrationsHint', { failing: webhookOverview.failing }) }}</small>
            </article>
            <article>
              <span class="command-deck-eyebrow">{{ t('admin.system.discordBot.eyebrow') }}</span>
              <strong>{{ t('admin.system.discordBot.title') }}</strong>
              <p>{{ t('admin.system.discordBot.subtitle') }}</p>
              <button class="small-action" type="button" @click="navigateToTab('status')">{{ t('admin.tabs.status') }}</button>
            </article>
            <article class="is-private">
              <span class="command-deck-eyebrow">{{ t('admin.workspace.adminGroup') }}</span>
              <strong>{{ t('admin.workspace.adminScopeTitle') }}</strong>
              <p>{{ t('admin.workspace.adminScopeText') }}</p>
            </article>
          </div>
          <OutboundWebhookManagementPanel :can-manage="true" />
        </section>

        <section v-if="activeTab === 'calendar'" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading">
            <div><h2>{{ t('admin.calendar.title') }}</h2><p>{{ t('admin.calendar.subtitle') }}</p></div>
            <div class="hero-actions"><span class="summary-pill">{{ eventCountLabel }}</span><RouterLink class="button-box primary-action" to="/calendar/new">{{ t('calendar.list.newEvent') }}</RouterLink></div>
          </div>
          <div class="staff-filter-surface">
            <div class="staff-filter-surface-head">
              <div><strong>{{ t('admin.workspace.filters.title') }}</strong><small>{{ t('admin.workspace.filters.calendarHint') }}</small></div>
              <div class="hero-actions"><RouterLink class="small-action" to="/calendar">{{ t('admin.calendar.openCalendar') }}</RouterLink><button class="small-action" type="button" @click="resetCalendarFilters">{{ t('admin.workspace.filters.reset') }}</button></div>
            </div>
            <div class="staff-filter-row staff-filter-row--wide">
              <label class="filter-box admin-search"><input v-model="calendarSearch" type="search" :placeholder="t('admin.workspace.filters.calendarSearch')" /></label>
              <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="calendarCategory"><option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.from') }}</span><input v-model="calendarFromDate" type="date" /></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.to') }}</span><input v-model="calendarToDate" type="date" /></label>
            </div>
          </div>
          <p v-if="calendarLoading" class="muted table-state">{{ t('admin.calendar.loading') }}</p>
          <p v-else-if="calendarError" class="error-text table-state">{{ calendarError }}</p>
          <p v-else-if="upcomingEvents.length === 0" class="muted table-state">{{ t('admin.calendar.empty') }}</p>
          <div v-else class="admin-build-list staff-event-list">
            <article v-for="event in upcomingEvents" :key="event.id" class="admin-build-row staff-event-row">
              <div class="admin-build-main">
                <strong>{{ event.title }}</strong>
                <span>{{ t(`calendar.categories.${event.category}`) }} · {{ formatEventRange(event) }}<template v-if="event.location"> · {{ event.location }}</template></span>
              </div>
              <div v-if="isPending('event', event.id)" class="delete-confirmation"><span>{{ t('admin.calendar.confirmCancel') }}</span><button class="danger-action" type="button" @click="confirmDeleteEvent(event.id)">{{ t('admin.calendar.cancelNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div>
              <button v-else class="danger-action" type="button" @click="askDelete('event', event.id)">{{ t('admin.calendar.cancel') }}</button>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'content'" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.content.title') }}</h2><p>{{ t('admin.content.subtitle') }}</p></div><span class="summary-pill">{{ contentCountLabel }}</span></div>
          <div class="staff-filter-surface">
            <div class="staff-filter-surface-head"><div><strong>{{ t('admin.workspace.filters.title') }}</strong><small>{{ t('admin.workspace.filters.contentHint') }}</small></div><button class="small-action" type="button" @click="resetContentFilters">{{ t('admin.workspace.filters.reset') }}</button></div>
            <div class="staff-filter-row staff-filter-row--wide">
              <label class="filter-box admin-search"><input v-model="contentSearch" type="search" :placeholder="t('admin.content.searchPlaceholder')" /></label>
              <label class="filter-box select-shell"><select v-model="contentScope"><option value="all">{{ t('admin.workspace.filters.allContent') }}</option><option value="forum">{{ t('admin.content.forum') }}</option><option value="guides">{{ t('admin.content.guides') }}</option><option value="groups">{{ t('admin.content.announcements') }}</option></select></label>
              <label class="filter-box admin-search"><input v-model="contentOwner" type="search" :placeholder="t('admin.workspace.filters.ownerSearch')" /></label>
            </div>
          </div>
          <p v-if="contentLoading" class="muted table-state">{{ t('admin.content.loading') }}</p>
          <p v-else-if="contentError" class="error-text table-state">{{ contentError }}</p>
          <div class="staff-content-grid" :class="{ 'is-single-scope': contentScope !== 'all' }">
            <section v-if="contentScope === 'all' || contentScope === 'forum'" class="staff-content-column"><h3>{{ t('admin.content.forum') }}</h3><p v-if="visibleForumThreads.length === 0" class="muted table-state">{{ t('admin.content.emptyForum') }}</p><article v-for="thread in visibleForumThreads" :key="thread.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ thread.title }}</strong><span>{{ thread.category }} · {{ thread.owner.display_name }} · {{ t('admin.content.replies', { count: thread.reply_count }) }}</span></div><div v-if="isPending('thread', thread.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteThread(thread.id)">{{ t('admin.content.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('thread', thread.id)">{{ t('admin.content.delete') }}</button></article></section>
            <section v-if="contentScope === 'all' || contentScope === 'guides'" class="staff-content-column"><h3>{{ t('admin.content.guides') }}</h3><p v-if="visibleGuides.length === 0" class="muted table-state">{{ t('admin.content.emptyGuides') }}</p><article v-for="guide in visibleGuides" :key="guide.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ guide.title }}</strong><span>{{ guide.category }} · {{ guide.owner.display_name }} · {{ t('admin.content.attachments', { count: guide.attachment_count }) }}</span></div><div v-if="isPending('guide', guide.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteGuide(guide.id)">{{ t('admin.content.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('guide', guide.id)">{{ t('admin.content.delete') }}</button></article></section>
            <section v-if="contentScope === 'all' || contentScope === 'groups'" class="staff-content-column"><h3>{{ t('admin.content.announcements') }}</h3><p v-if="visibleGroups.length === 0" class="muted table-state">{{ t('admin.content.emptyGroups') }}</p><article v-for="group in visibleGroups" :key="group.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ group.title }}</strong><span>{{ t(`focus.${group.focus}`) }} · {{ group.owner.display_name }} · {{ t('admin.content.members', { count: group.active_members_count }) }}</span></div><div v-if="isPending('group', group.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmClose') }}</span><button class="danger-action" type="button" @click="confirmCloseGroup(group.id)">{{ t('admin.content.closeNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('group', group.id)">{{ t('admin.content.close') }}</button></article></section>
          </div>
        </section>

        <section v-if="activeTab === 'builds'" class="wire-section admin-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.builds.title') }}</h2><p>{{ t('admin.builds.subtitle') }}</p></div><span class="summary-pill">{{ buildCountLabel }}</span></div>
          <div class="staff-filter-surface">
            <div class="staff-filter-surface-head"><div><strong>{{ t('admin.workspace.filters.title') }}</strong><small>{{ t('admin.workspace.filters.buildHint') }}</small></div><button class="small-action" type="button" @click="resetBuildFilters">{{ t('admin.workspace.filters.reset') }}</button></div>
            <div class="staff-filter-row staff-filter-row--wide">
              <label class="filter-box admin-search"><input v-model="search" type="search" :placeholder="t('admin.builds.searchPlaceholder')" /></label>
              <label class="filter-box select-shell"><select v-model="buildType"><option value="">{{ t('admin.workspace.filters.allBuildTypes') }}</option><option value="balanced">{{ t('builds.types.balanced') }}</option><option value="gunnery">{{ t('builds.types.gunnery') }}</option><option value="boarding">{{ t('builds.types.boarding') }}</option><option value="defensive">{{ t('builds.types.defensive') }}</option></select></label>
              <label class="filter-box select-shell"><select v-model="buildRate"><option value="">{{ t('admin.workspace.filters.allRates') }}</option><option v-for="rate in buildRates" :key="rate" :value="String(rate)">{{ t('common.rate') }} {{ rate }}</option></select></label>
              <label class="filter-box select-shell"><select v-model="buildVisibility"><option value="">{{ t('admin.workspace.filters.allSources') }}</option><option value="official">{{ t('admin.workspace.filters.officialBuilds') }}</option><option value="community">{{ t('admin.workspace.filters.communityBuilds') }}</option></select></label>
            </div>
          </div>
          <p v-if="loading" class="muted table-state">{{ t('admin.builds.loading') }}</p><p v-else-if="error" class="error-text table-state">{{ error }}</p><p v-else-if="filteredBuilds.length === 0" class="muted table-state">{{ t('admin.builds.empty') }}</p>
          <div v-else class="admin-build-list"><article v-for="build in filteredBuilds" :key="build.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ build.build_name }}</strong><span>{{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ t(`builds.types.${build.build_type}`) }} · {{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}</span><small v-if="build.is_official_template" class="summary-pill staff-inline-pill">{{ t('admin.workspace.filters.officialBuilds') }}</small></div><div v-if="isPending('build', build.id)" class="delete-confirmation"><span>{{ t('admin.builds.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteBuild(build.id)">{{ t('admin.builds.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('build', build.id)">{{ t('admin.builds.delete') }}</button></article></div>
        </section>

        <section v-if="activeTab === 'users' && isAdmin" class="wire-section admin-panel admin-users-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.users.title') }}</h2><p>{{ t('admin.users.subtitle') }}</p></div><span class="summary-pill">{{ userCountLabel }}</span></div>
          <form class="moderator-form" @submit.prevent="submitModerator"><label class="input-panel embedded-field"><span>{{ t('auth.username') }}</span><input v-model="moderatorForm.username" required minlength="3" maxlength="80" /></label><label class="input-panel embedded-field"><span>{{ t('profile.displayName') }}</span><input v-model="moderatorForm.display_name" required maxlength="120" /></label><label class="input-panel embedded-field"><span>{{ t('auth.password') }}</span><input v-model="moderatorForm.password" type="password" required minlength="12" /></label><button class="form-button primary-action" type="submit">{{ t('admin.users.createModerator') }}</button></form>
          <div class="staff-filter-surface">
            <div class="staff-filter-surface-head"><div><strong>{{ t('admin.workspace.filters.title') }}</strong><small>{{ t('admin.workspace.filters.userHint') }}</small></div><button class="small-action" type="button" @click="resetUserFilters">{{ t('admin.workspace.filters.reset') }}</button></div>
            <div class="staff-filter-row staff-filter-row--wide">
              <label class="filter-box admin-search"><input v-model="userSearch" type="search" :placeholder="t('admin.workspace.filters.userSearch')" /></label>
              <label class="filter-box select-shell"><select v-model="userRole"><option value="">{{ t('admin.workspace.filters.allRoles') }}</option><option value="admin">{{ t('roles.admin') }}</option><option value="moderator">{{ t('roles.moderator') }}</option><option value="user">{{ t('roles.user') }}</option></select></label>
              <label class="filter-box select-shell"><select v-model="userStatus"><option value="">{{ t('admin.workspace.filters.allStatuses') }}</option><option value="active">{{ t('fleets.status.active') }}</option><option value="inactive">{{ t('fleets.status.inactive') }}</option></select></label>
            </div>
          </div>
          <p v-if="userLoading" class="muted table-state">{{ t('admin.users.loading') }}</p><p v-if="userError" class="error-text table-state">{{ userError }}</p><p v-if="moderatorSuccess" class="success-text table-state">{{ moderatorSuccess }}</p>
          <p v-if="!userLoading && filteredUsers.length === 0" class="muted table-state">{{ t('admin.workspace.filters.noResults') }}</p>
          <div v-else class="admin-user-list">
            <article v-for="row in filteredUsers" :key="row.id" class="admin-user-row">
              <div><strong>{{ row.display_name }}</strong><span>{{ row.username }}</span></div>
              <span class="summary-pill">{{ t(`roles.${row.role}`) }}</span>
              <span class="summary-pill">{{ row.is_active ? t('fleets.status.active') : t('fleets.status.inactive') }}</span>
              <div v-if="canManageUser(row)" class="compact-actions">
                <select :value="row.role" @change="changeUserRole(row, $event)">
                  <option value="user">{{ t('roles.user') }}</option>
                  <option value="moderator">{{ t('roles.moderator') }}</option>
                </select>
                <button class="small-action" type="button" @click="toggleUserActive(row)">
                  {{ row.is_active ? t('fleets.status.inactive') : t('fleets.status.active') }}
                </button>
              </div>
              <small v-else class="muted">{{ row.id === user?.id ? t('common.profile') : t(`roles.${row.role}`) }}</small>
            </article>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>
