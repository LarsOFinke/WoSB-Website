<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import {
  createModerator,
  deleteAdminBuild,
  deleteAdminForumThread,
  deleteAdminGuide,
  listAdminBuilds,
  listAdminForumThreads,
  listAdminGuides,
  listUsers,
} from '@/services/admin'
import { closeGroup, listGroups } from '@/services/groups'
import { deleteFleetEvent, FLEET_EVENT_CATEGORIES, listFleetEvents } from '@/services/fleetCalendar'
import { useSession } from '@/services/session'

const { locale, t } = useLocale()
const { isAdmin, isStaff, loadSession, sessionState, user } = useSession()

const activeTab = ref('status')
const builds = ref([])
const users = ref([])
const fleetEvents = ref([])
const forumThreads = ref([])
const guides = ref([])
const groups = ref([])
const search = ref('')
const contentSearch = ref('')
const calendarCategory = ref('')
const loading = ref(false)
const userLoading = ref(false)
const calendarLoading = ref(false)
const contentLoading = ref(false)
const error = ref('')
const userError = ref('')
const calendarError = ref('')
const contentError = ref('')
const moderatorSuccess = ref('')
const pendingDelete = reactive({ type: '', id: null })
const apiStatus = ref(t('admin.status.loading'))
const apiStatusDetail = ref(t('admin.status.loadingDetail'))
let searchTimer = null
let contentTimer = null

const moderatorForm = reactive({ username: '', display_name: '', password: '' })

const buildCountLabel = computed(() => builds.value.length === 1 ? t('admin.builds.summaryOne') : t('admin.builds.summaryMany', { count: builds.value.length }))
const userCountLabel = computed(() => users.value.length === 1 ? t('admin.users.summaryOne') : t('admin.users.summaryMany', { count: users.value.length }))
const eventCountLabel = computed(() => fleetEvents.value.length === 1 ? t('admin.calendar.summaryOne') : t('admin.calendar.summaryMany', { count: fleetEvents.value.length }))
const contentCountLabel = computed(() => t('admin.content.summary', { count: forumThreads.value.length + guides.value.length + groups.value.length }))
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

watch(search, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

watch(contentSearch, () => {
  window.clearTimeout(contentTimer)
  contentTimer = window.setTimeout(loadContent, 220)
})

watch(calendarCategory, loadCalendar)

watch(activeTab, async (tab) => {
  clearConfirmation()
  if (tab === 'builds') await loadBuilds()
  if (tab === 'status') await loadStatus()
  if (tab === 'users') await loadUsers()
  if (tab === 'calendar') await loadCalendar()
  if (tab === 'content') await loadContent()
})

onMounted(async () => {
  if (!sessionState.isReady) await loadSession()
  await loadStatus()
})
</script>

<template>
  <section class="admin-page" aria-labelledby="admin-title">
    <div class="wire-frame page-frame admin-frame staff-workspace-frame">
      <header class="wire-section admin-hero refined-admin-hero staff-hero">
        <div>
          <p class="eyebrow">{{ t('admin.eyebrow') }}</p>
          <h1 id="admin-title">{{ isAdmin ? t('admin.title') : t('admin.moderatorTitle') }}</h1>
          <p>{{ isAdmin ? t('admin.subtitle') : t('admin.moderatorSubtitle') }}</p>
        </div>
        <div class="staff-hero-actions">
          <span v-if="user" class="summary-pill">{{ t(`roles.${user.role}`) }}</span>
          <RouterLink v-if="isStaff" class="button-box primary-action" to="/calendar/new">{{ t('admin.quickActions.newEvent') }}</RouterLink>
        </div>
      </header>

      <section v-if="!isStaff" class="wire-section admin-locked">
        <h2>{{ t('admin.lockedTitle') }}</h2>
        <p>{{ t('admin.lockedText') }}</p>
        <RouterLink class="button-box primary-action" to="/login">{{ t('auth.login') }}</RouterLink>
      </section>

      <template v-else>
        <section class="wire-section staff-command-center" aria-label="Staff quick actions">
          <RouterLink class="staff-command-card" to="/calendar/new">
            <span>{{ t('admin.quickActions.scheduleLabel') }}</span>
            <strong>{{ t('admin.quickActions.newEvent') }}</strong>
            <small>{{ t('admin.quickActions.scheduleText') }}</small>
          </RouterLink>
          <RouterLink class="staff-command-card" to="/forum/new">
            <span>{{ t('admin.quickActions.forumLabel') }}</span>
            <strong>{{ t('admin.quickActions.newThread') }}</strong>
            <small>{{ t('admin.quickActions.forumText') }}</small>
          </RouterLink>
          <RouterLink class="staff-command-card" to="/guides/new">
            <span>{{ t('admin.quickActions.guidesLabel') }}</span>
            <strong>{{ t('admin.quickActions.newGuide') }}</strong>
            <small>{{ t('admin.quickActions.guidesText') }}</small>
          </RouterLink>
          <RouterLink class="staff-command-card" to="/fleets/manage">
            <span>{{ t('fleets.manage.eyebrow') }}</span>
            <strong>{{ t('common.fleetManagement') }}</strong>
            <small>{{ t('fleets.manage.subtitle') }}</small>
          </RouterLink>
        </section>

        <section class="wire-section admin-tabs staff-tabs" :aria-label="t('admin.tabsLabel')">
          <button class="tab-button" :class="{ 'is-active': activeTab === 'status' }" type="button" @click="activeTab = 'status'">{{ t('admin.tabs.status') }}</button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'calendar' }" type="button" @click="activeTab = 'calendar'">{{ t('admin.tabs.calendar') }}</button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'content' }" type="button" @click="activeTab = 'content'">{{ t('admin.tabs.content') }}</button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'builds' }" type="button" @click="activeTab = 'builds'">{{ t('admin.tabs.builds') }}</button>
          <button v-if="isAdmin" class="tab-button" :class="{ 'is-active': activeTab === 'users' }" type="button" @click="activeTab = 'users'">{{ t('admin.tabs.users') }}</button>
        </section>

        <section v-if="activeTab === 'status'" class="wire-section admin-panel admin-status-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.status.title') }}</h2><p>{{ t('admin.status.subtitle') }}</p></div></div>
          <aside class="home-status-card refined-status-card admin-status-card" aria-live="polite">
            <span>{{ t('admin.status.cardLabel') }}</span><strong>{{ apiStatus }}</strong><p>{{ apiStatusDetail }}</p>
          </aside>
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
          <form class="moderator-form" @submit.prevent="submitModerator"><label class="input-panel embedded-field"><span>{{ t('auth.username') }}</span><input v-model="moderatorForm.username" required minlength="3" maxlength="80" /></label><label class="input-panel embedded-field"><span>{{ t('profile.displayName') }}</span><input v-model="moderatorForm.display_name" required maxlength="120" /></label><label class="input-panel embedded-field"><span>{{ t('auth.password') }}</span><input v-model="moderatorForm.password" type="password" required minlength="6" /></label><button class="form-button primary-action" type="submit">{{ t('admin.users.createModerator') }}</button></form>
          <p v-if="userLoading" class="muted table-state">{{ t('admin.users.loading') }}</p><p v-if="userError" class="error-text table-state">{{ userError }}</p><p v-if="moderatorSuccess" class="success-text table-state">{{ moderatorSuccess }}</p>
          <div class="admin-user-list"><article v-for="row in users" :key="row.id" class="admin-user-row"><div><strong>{{ row.display_name }}</strong><span>{{ row.username }}</span></div><span class="summary-pill">{{ t(`roles.${row.role}`) }}</span></article></div>
        </section>
      </template>
    </div>
  </section>
</template>
