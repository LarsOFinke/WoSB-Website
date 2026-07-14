<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import SystemOperationsPanel from '@/modules/admin/components/SystemOperationsPanel.vue'
import SecurityLogDashboard from '@/modules/admin/components/SecurityLogDashboard.vue'
import AuditLogPanel from '@/modules/admin/components/AuditLogPanel.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import {
  approveRegistrationRequest,
  createModerator,
  deleteAdminBuild,
  deleteAdminForumThread,
  deleteAdminGuide,
  getAdminLogSummary,
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
const isoDate = (value) => value.toISOString().slice(0, 10)

const activeTab = ref('status')
const builds = ref([])
const users = ref([])
const fleetEvents = ref([])
const forumThreads = ref([])
const guides = ref([])
const groups = ref([])
const registrationRequests = ref([])
const appLogs = ref([])
const logSummary = ref({ total: 0, errors: 0, warnings: 0, slow_requests: 0, recent_status: {} })
const search = ref('')
const contentSearch = ref('')
const calendarCategory = ref('')
const registrationStatus = ref('pending')
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
let contentTimer = null
let logFilterTimer = null

const moderatorForm = reactive({ username: '', display_name: '', password: '' })

const buildCountLabel = computed(() => builds.value.length === 1 ? t('admin.builds.summaryOne') : t('admin.builds.summaryMany', { count: builds.value.length }))
const userCountLabel = computed(() => users.value.length === 1 ? t('admin.users.summaryOne') : t('admin.users.summaryMany', { count: users.value.length }))
const eventCountLabel = computed(() => fleetEvents.value.length === 1 ? t('admin.calendar.summaryOne') : t('admin.calendar.summaryMany', { count: fleetEvents.value.length }))
const contentCountLabel = computed(() => t('admin.content.summary', { count: forumThreads.value.length + guides.value.length + groups.value.length }))
const registrationCountLabel = computed(() => registrationRequests.value.length === 1 ? t('admin.registrations.summaryOne') : t('admin.registrations.summaryMany', { count: registrationRequests.value.length }))
const logsCountLabel = computed(() => t('admin.logs.summary', { count: logSummary.value.total || appLogs.value.length }))
const upcomingEvents = computed(() => [...fleetEvents.value].sort((a, b) => new Date(a.start_at) - new Date(b.start_at)).slice(0, 12))
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
    builds.value = await listAdminBuilds(search.value)
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
  if (!isStaff.value) return
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

async function loadRegistrations() {
  if (!isAdmin.value) return
  registrationLoading.value = true
  registrationError.value = ''
  try {
    registrationRequests.value = await listRegistrationRequests(registrationStatus.value)
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
  if (!isStaff.value) return
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

async function loadCalendar() {
  if (!isStaff.value) return
  calendarLoading.value = true
  calendarError.value = ''
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setDate(end.getDate() + 90)
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

watch(search, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

watch(contentSearch, () => {
  window.clearTimeout(contentTimer)
  contentTimer = window.setTimeout(loadContent, 220)
})

watch(calendarCategory, loadCalendar)
watch(registrationStatus, loadRegistrations)
watch([logLevel, logIp, logThreat, logFromDate, logToDate, logSort, logOrder], loadLogs)
watch(logPath, () => {
  window.clearTimeout(logFilterTimer)
  logFilterTimer = window.setTimeout(loadLogs, 260)
})

watch(activeTab, async (tab) => {
  clearConfirmation()
  if (tab === 'builds') await loadBuilds()
  if (tab === 'status') await loadStatus()
  if (tab === 'users') await loadUsers()
  if (tab === 'registrations') await loadRegistrations()
  if (tab === 'logs') await loadLogs()
  if (tab === 'calendar') await loadCalendar()
  if (tab === 'content') await loadContent()
})

onMounted(async () => {
  if (!sessionState.isReady) await loadSession()
  await Promise.all([loadStatus(), loadLogs()])
  if (isAdmin.value) await loadRegistrations()
})

onUnmounted(() => {
  window.clearTimeout(searchTimer)
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
          <span class="summary-pill" :class="{ 'fleet-status-pill': apiStatus === t('admin.status.online') }">{{ apiStatus }}</span>
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

        <section class="wire-section admin-tabs staff-tabs workspace-tab-rail" :aria-label="t('admin.tabsLabel')">
          <button class="tab-button" :class="{ 'is-active': activeTab === 'status' }" type="button" @click="activeTab = 'status'"><span><AppIcon name="activity" :size="17" />{{ t('admin.tabs.status') }}</span></button>
          <button v-if="isAdmin" class="tab-button" :class="{ 'is-active': activeTab === 'registrations' }" type="button" @click="activeTab = 'registrations'"><span><AppIcon name="inbox" :size="17" />{{ t('admin.tabs.registrations') }}</span></button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'logs' }" type="button" @click="activeTab = 'logs'"><span><AppIcon name="activity" :size="17" />{{ t('admin.tabs.logs') }}</span></button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'audit' }" type="button" @click="activeTab = 'audit'"><span><AppIcon name="inbox" :size="17" />{{ t('admin.tabs.audit') }}</span></button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'calendar' }" type="button" @click="activeTab = 'calendar'"><span><AppIcon name="calendar" :size="17" />{{ t('admin.tabs.calendar') }}</span></button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'content' }" type="button" @click="activeTab = 'content'"><span><AppIcon name="forum" :size="17" />{{ t('admin.tabs.content') }}</span></button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'builds' }" type="button" @click="activeTab = 'builds'"><span><AppIcon name="builds" :size="17" />{{ t('admin.tabs.builds') }}</span></button>
          <button v-if="isAdmin" class="tab-button" :class="{ 'is-active': activeTab === 'users' }" type="button" @click="activeTab = 'users'"><span><AppIcon name="users" :size="17" />{{ t('admin.tabs.users') }}</span></button>
        </section>

        <section v-if="activeTab === 'status'" class="wire-section admin-panel admin-status-panel">
          <SystemOperationsPanel :api-status="apiStatus" :api-status-detail="apiStatusDetail" :is-admin="isAdmin" @refresh-api="loadStatus" />

          <div class="workspace-metric-grid admin-dashboard-grid">
            <MetricCard v-if="isAdmin" :label="t('admin.registrations.dashboardLabel')" :value="registrationRequests.length" :hint="t('admin.registrations.dashboardHint')" tone="accent" />
            <MetricCard :label="t('admin.logs.total')" :value="logSummary.total" :hint="t('admin.logs.dashboardHint')" />
            <MetricCard :label="t('admin.logs.errors')" :value="logSummary.errors" :hint="t('admin.logs.errorHint')" tone="danger" />
            <MetricCard :label="t('admin.logs.slowRequests')" :value="logSummary.slow_requests" :hint="t('admin.logs.slowHint')" />
          </div>
        </section>

        <section v-if="activeTab === 'registrations' && isAdmin" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading">
            <div><h2>{{ t('admin.registrations.title') }}</h2><p>{{ t('admin.registrations.subtitle') }}</p></div>
            <span class="summary-pill">{{ registrationCountLabel }}</span>
          </div>
          <div class="staff-filter-row">
            <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="registrationStatus"><option value="pending">{{ t('admin.registrations.status.pending') }}</option><option value="approved">{{ t('admin.registrations.status.approved') }}</option><option value="rejected">{{ t('admin.registrations.status.rejected') }}</option><option value="">{{ t('admin.registrations.status.all') }}</option></select></label>
          </div>
          <p v-if="registrationLoading" class="muted table-state">{{ t('admin.registrations.loading') }}</p>
          <p v-else-if="registrationError" class="error-text table-state">{{ registrationError }}</p>
          <p v-else-if="registrationRequests.length === 0" class="muted table-state">{{ t('admin.registrations.empty') }}</p>
          <div v-else class="admin-build-list registration-review-list">
            <article v-for="request in registrationRequests" :key="request.id" class="admin-build-row registration-review-row">
              <div class="admin-build-main">
                <strong>{{ request.display_name }}</strong>
                <span>{{ request.username }} · {{ formatDateTime(request.created_at) }} · {{ t(`admin.registrations.status.${request.status}`) }}</span>
                <p v-if="request.decision_note" class="muted">{{ t('admin.registrations.decisionNote') }}: {{ request.decision_note }}</p>
              </div>
              <div v-if="request.status === 'pending'" class="registration-actions">
                <label class="input-panel embedded-field"><span>{{ t('admin.registrations.noteLabel') }}</span><input v-model="registrationDecisionNotes[request.id]" maxlength="1000" :placeholder="t('admin.registrations.notePlaceholder')" /></label>
                <div class="hero-actions"><button class="form-button primary-action" type="button" @click="approveRegistration(request.id)">{{ t('admin.registrations.approve') }}</button><button class="danger-action" type="button" @click="rejectRegistration(request.id)">{{ t('admin.registrations.reject') }}</button></div>
              </div>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'logs'" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.logs.title') }}</h2><p>{{ t('admin.logs.subtitle') }}</p></div><div class="hero-actions"><span class="summary-pill">{{ logsCountLabel }}</span><button class="small-action" type="button" :disabled="logsLoading" @click="loadLogs">{{ t('admin.logs.refresh') }}</button></div></div>
          <div class="staff-log-workspace">
            <SecurityLogDashboard
              v-model:from-date="logFromDate"
              v-model:to-date="logToDate"
              v-model:threat-level="logThreat"
              v-model:selected-ip="logIp"
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

        <section v-if="activeTab === 'audit'" class="wire-section admin-panel staff-management-panel">
          <AuditLogPanel />
        </section>

        <section v-if="activeTab === 'calendar'" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading">
            <div><h2>{{ t('admin.calendar.title') }}</h2><p>{{ t('admin.calendar.subtitle') }}</p></div>
            <div class="hero-actions"><span class="summary-pill">{{ eventCountLabel }}</span><RouterLink class="button-box primary-action" to="/calendar/new">{{ t('calendar.list.newEvent') }}</RouterLink></div>
          </div>
          <div class="staff-filter-row">
            <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="calendarCategory"><option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
            <RouterLink class="small-action" to="/calendar">{{ t('admin.calendar.openCalendar') }}</RouterLink>
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
          <label class="filter-box admin-search"><input v-model="contentSearch" type="search" :placeholder="t('admin.content.searchPlaceholder')" /></label>
          <p v-if="contentLoading" class="muted table-state">{{ t('admin.content.loading') }}</p>
          <p v-else-if="contentError" class="error-text table-state">{{ contentError }}</p>
          <div class="staff-content-grid">
            <section class="staff-content-column"><h3>{{ t('admin.content.forum') }}</h3><p v-if="forumThreads.length === 0" class="muted table-state">{{ t('admin.content.emptyForum') }}</p><article v-for="thread in forumThreads" :key="thread.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ thread.title }}</strong><span>{{ thread.category }} · {{ thread.owner.display_name }} · {{ t('admin.content.replies', { count: thread.reply_count }) }}</span></div><div v-if="isPending('thread', thread.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteThread(thread.id)">{{ t('admin.content.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('thread', thread.id)">{{ t('admin.content.delete') }}</button></article></section>
            <section class="staff-content-column"><h3>{{ t('admin.content.guides') }}</h3><p v-if="guides.length === 0" class="muted table-state">{{ t('admin.content.emptyGuides') }}</p><article v-for="guide in guides" :key="guide.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ guide.title }}</strong><span>{{ guide.category }} · {{ guide.owner.display_name }} · {{ t('admin.content.attachments', { count: guide.attachment_count }) }}</span></div><div v-if="isPending('guide', guide.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteGuide(guide.id)">{{ t('admin.content.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('guide', guide.id)">{{ t('admin.content.delete') }}</button></article></section>
            <section class="staff-content-column"><h3>{{ t('admin.content.announcements') }}</h3><p v-if="groups.length === 0" class="muted table-state">{{ t('admin.content.emptyGroups') }}</p><article v-for="group in groups" :key="group.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ group.title }}</strong><span>{{ t(`focus.${group.focus}`) }} · {{ group.owner.display_name }} · {{ t('admin.content.members', { count: group.active_members_count }) }}</span></div><div v-if="isPending('group', group.id)" class="delete-confirmation"><span>{{ t('admin.content.confirmClose') }}</span><button class="danger-action" type="button" @click="confirmCloseGroup(group.id)">{{ t('admin.content.closeNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('group', group.id)">{{ t('admin.content.close') }}</button></article></section>
          </div>
        </section>

        <section v-if="activeTab === 'builds'" class="wire-section admin-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.builds.title') }}</h2><p>{{ t('admin.builds.subtitle') }}</p></div><span class="summary-pill">{{ buildCountLabel }}</span></div>
          <label class="filter-box admin-search"><input v-model="search" type="search" :placeholder="t('admin.builds.searchPlaceholder')" /></label>
          <p v-if="loading" class="muted table-state">{{ t('admin.builds.loading') }}</p><p v-else-if="error" class="error-text table-state">{{ error }}</p><p v-else-if="builds.length === 0" class="muted table-state">{{ t('admin.builds.empty') }}</p>
          <div v-else class="admin-build-list"><article v-for="build in builds" :key="build.id" class="admin-build-row"><div class="admin-build-main"><strong>{{ build.build_name }}</strong><span>{{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ t(`builds.types.${build.build_type}`) }} · {{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}</span></div><div v-if="isPending('build', build.id)" class="delete-confirmation"><span>{{ t('admin.builds.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteBuild(build.id)">{{ t('admin.builds.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('build', build.id)">{{ t('admin.builds.delete') }}</button></article></div>
        </section>

        <section v-if="activeTab === 'users' && isAdmin" class="wire-section admin-panel admin-users-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.users.title') }}</h2><p>{{ t('admin.users.subtitle') }}</p></div><span class="summary-pill">{{ userCountLabel }}</span></div>
          <form class="moderator-form" @submit.prevent="submitModerator"><label class="input-panel embedded-field"><span>{{ t('auth.username') }}</span><input v-model="moderatorForm.username" required minlength="3" maxlength="80" /></label><label class="input-panel embedded-field"><span>{{ t('profile.displayName') }}</span><input v-model="moderatorForm.display_name" required maxlength="120" /></label><label class="input-panel embedded-field"><span>{{ t('auth.password') }}</span><input v-model="moderatorForm.password" type="password" required minlength="12" /></label><button class="form-button primary-action" type="submit">{{ t('admin.users.createModerator') }}</button></form>
          <p v-if="userLoading" class="muted table-state">{{ t('admin.users.loading') }}</p><p v-if="userError" class="error-text table-state">{{ userError }}</p><p v-if="moderatorSuccess" class="success-text table-state">{{ moderatorSuccess }}</p>
          <div class="admin-user-list">
            <article v-for="row in users" :key="row.id" class="admin-user-row">
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
