<script setup>
import { computed, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import AuditLogPanel from '@/modules/admin/components/AuditLogPanel.vue'
import IpBlockManagementPanel from '@/modules/admin/components/IpBlockManagementPanel.vue'
import SecurityLogDashboard from '@/modules/admin/components/SecurityLogDashboard.vue'
import StaffOverviewPanel from '@/modules/admin/components/StaffOverviewPanel.vue'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import SystemOperationsPanel from '@/modules/admin/components/SystemOperationsPanel.vue'
import { useAdminWorkspace } from '@/modules/admin/composables/useAdminWorkspace'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const {
  locale, t, isAdmin, isStaff, user, activeTab,
  builds, users, fleetEvents, forumThreads, guides, groups, registrationRequests, appLogs,
  ipBlockPrefill, logSummary, ipBlockOverview, overviewLoading,
  search, contentSearch, calendarCategory, registrationStatus, registrationSearch,
  registrationFromDate, registrationToDate, calendarSearch, calendarFromDate, calendarToDate,
  contentScope, contentOwner, buildType, buildRate, buildVisibility, userSearch, userRole,
  userStatus, logLevel, logPath, logIp, logThreat, logFromDate, logToDate, logSort, logOrder,
  loading, userLoading, calendarLoading, contentLoading, registrationLoading, logsLoading,
  error, userError, calendarError, contentError, registrationError, logsError, moderatorSuccess,
  pendingDelete, registrationDecisionNotes, apiStatus, apiStatusDetail, moderatorForm,
  filteredBuilds, filteredUsers, filteredEvents, upcomingEvents, visibleForumThreads, visibleGuides,
  visibleGroups, visibleContentCount, pendingRegistrationRows, oldestPendingRequest,
  nextOverviewEvent, buildRates, buildCountLabel, userCountLabel, eventCountLabel,
  contentCountLabel, registrationCountLabel, logsCountLabel, categoryOptions,
  crewTotal, formatDateTime, formatEventRange, clearConfirmation, isPending, askDelete,
  loadBuilds, loadUsers, loadStatus, loadAdminOverviewMetrics, loadOverview, loadRegistrations,
  approveRegistration, rejectRegistration, loadLogs, formatDuration, openIpBlockManager,
  openLogsForIp, loadCalendar, loadContent, confirmDeleteBuild, confirmDeleteEvent,
  confirmDeleteThread, confirmDeleteGuide, confirmCloseGroup, submitModerator,
  changeUserRole, toggleUserActive, canManageUser, navigateToTab, resetRegistrationFilters,
  resetCalendarFilters, resetContentFilters, resetBuildFilters, resetUserFilters, canAccessTab,
} = useAdminWorkspace()

const expandedLogId = ref(null)
const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
const activeLogFilterCount = computed(() => [logLevel.value, logPath.value, logIp.value, logThreat.value].filter(Boolean).length)

function isoDate(value) {
  return value.toISOString().slice(0, 10)
}

function setLogRange(days) {
  const end = new Date()
  const start = new Date(end)
  start.setDate(end.getDate() - Math.max(0, days - 1))
  logFromDate.value = isoDate(start)
  logToDate.value = isoDate(end)
}

function resetLogFilters() {
  logLevel.value = ''
  logPath.value = ''
  logIp.value = ''
  logThreat.value = ''
  logSort.value = 'created_at'
  logOrder.value = 'desc'
  setLogRange(7)
}

</script>
<template>
  <StaffWorkspaceShell
    v-if="isStaff"
    :eyebrow="t('admin.eyebrow')"
    :title="isAdmin ? t('admin.title') : t('admin.moderatorTitle')"
    :description="isAdmin ? t('admin.subtitle') : t('admin.moderatorSubtitle')"
    title-id="admin-title"
    :groups="navigationGroups"
    :active-key="activeTab"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :status="isAdmin ? apiStatus : ''"
    :is-admin="isAdmin"
  >
    <template #actions>
      <RouterLink class="button-box" to="/calendar">{{ t('common.calendar') }}</RouterLink>
      <RouterLink class="button-box primary-action" to="/calendar/new">{{ t('admin.quickActions.newEvent') }}</RouterLink>
    </template>

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
                <div v-if="request.wants_fleet_membership" class="registration-fleet-request">
                  <strong>{{ t('admin.registrations.fleetApplication') }}</strong>
                  <p class="muted">{{ request.fleet_application_note || t('admin.registrations.fleetApplicationWithoutNote') }}</p>
                </div>
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
            <div class="staff-log-summary-strip">
              <article><span>{{ t('admin.logs.errors') }}</span><strong>{{ logSummary.errors }}</strong></article>
              <article><span>{{ t('admin.logs.warnings') }}</span><strong>{{ logSummary.warnings }}</strong></article>
              <article><span>{{ t('admin.logs.slowRequests') }}</span><strong>{{ logSummary.slow_requests }}</strong></article>
              <article><span>{{ t('admin.security.activeFilters', { count: activeLogFilterCount }) }}</span><strong>{{ logSummary.total }}</strong></article>
            </div>

            <article class="staff-log-surface log-filter-surface">
              <div class="staff-log-surface-head"><div><h3>{{ t('admin.logs.requestFilters') }}</h3><p>{{ t('admin.logs.requestFiltersHint') }}</p></div><button class="small-action" type="button" @click="resetLogFilters">{{ t('admin.security.resetFilters') }}</button></div>
              <div class="staff-log-quick-range"><button type="button" @click="setLogRange(1)">{{ t('admin.security.today') }}</button><button type="button" @click="setLogRange(7)">{{ t('admin.security.sevenDays') }}</button><button type="button" @click="setLogRange(30)">{{ t('admin.security.thirtyDays') }}</button></div>
              <div class="staff-filter-row log-filter-row refined-log-filter-row">
                <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="logLevel"><option value="">{{ t('admin.logs.levelAll') }}</option><option>INFO</option><option>WARNING</option><option>ERROR</option><option>CRITICAL</option></select></label>
                <label class="filter-box select-shell"><select v-model="logThreat"><option value="">{{ t('admin.security.allThreats') }}</option><option value="low">{{ t('admin.security.levels.low') }}</option><option value="guarded">{{ t('admin.security.levels.guarded') }}</option><option value="elevated">{{ t('admin.security.levels.elevated') }}</option><option value="critical">{{ t('admin.security.levels.critical') }}</option></select></label>
                <label class="filter-box admin-search"><input v-model="logPath" type="search" :placeholder="t('admin.logs.pathPlaceholder')" /></label>
                <label class="filter-box admin-search"><input v-model="logIp" type="search" :placeholder="t('admin.security.ipFilter')" /></label>
                <label class="filter-box select-shell"><select v-model="logSort"><option value="created_at">{{ t('admin.logs.sortDate') }}</option><option value="ip">{{ t('admin.logs.sortIp') }}</option><option value="status">{{ t('admin.logs.sortStatus') }}</option><option value="duration">{{ t('admin.logs.sortDuration') }}</option><option value="level">{{ t('admin.logs.sortLevel') }}</option></select></label>
                <label class="filter-box select-shell"><select v-model="logOrder"><option value="desc">{{ t('admin.logs.desc') }}</option><option value="asc">{{ t('admin.logs.asc') }}</option></select></label>
              </div>
              <div class="staff-log-active-scope" aria-live="polite"><strong>{{ logFromDate }} – {{ logToDate }}</strong><strong v-if="logThreat">{{ t(`admin.security.levels.${logThreat}`) }}</strong><strong v-if="logIp">{{ logIp }}</strong><strong v-if="logLevel">{{ logLevel }}</strong><strong v-if="logPath">{{ logPath }}</strong></div>
            </article>

            <details class="staff-log-security-disclosure">
              <summary><span>{{ t('admin.security.title') }}</span><small>{{ t('admin.security.subtitle') }}</small><AppIcon name="chevron-right" :size="17" /></summary>
              <SecurityLogDashboard v-model:from-date="logFromDate" v-model:to-date="logToDate" v-model:threat-level="logThreat" v-model:selected-ip="logIp" :can-block="isAdmin" @block-ip="openIpBlockManager" />
            </details>

            <article class="staff-log-surface log-results-surface">
              <div class="staff-log-surface-head"><div><h3>{{ t('admin.logs.resultsTitle') }}</h3><p>{{ t('admin.logs.resultsHint') }}</p></div><span class="summary-pill">{{ t('admin.logs.total') }} · {{ logSummary.total }}</span></div>
              <p v-if="logsLoading" class="muted table-state">{{ t('admin.logs.loading') }}</p>
              <p v-else-if="logsError" class="error-text table-state">{{ logsError }}</p>
              <p v-else-if="appLogs.length === 0" class="muted table-state">{{ t('admin.logs.empty') }}</p>
              <div v-else class="staff-log-list">
                <article v-for="entry in appLogs" :key="entry.id" class="staff-log-entry" :class="[`level-${(entry.level || 'info').toLowerCase()}`, { 'is-open': expandedLogId === entry.id }]">
                  <button class="staff-log-entry-summary" type="button" :aria-expanded="expandedLogId === entry.id" @click="expandedLogId = expandedLogId === entry.id ? null : entry.id">
                    <time>{{ formatDateTime(entry.created_at) }}</time>
                    <span class="staff-log-level-badge" :class="`level-${(entry.level || '').toLowerCase()}`">{{ entry.level }}</span>
                    <span class="staff-log-request"><strong>{{ entry.method || entry.logger }} <code>{{ entry.path || '—' }}</code></strong><small>{{ entry.message || entry.client_ip || '—' }}</small></span>
                    <span class="staff-log-response"><b :class="{ 'is-error': Number(entry.status_code) >= 400 }">{{ entry.status_code || '—' }}</b><small>{{ formatDuration(entry.duration_ms) }}</small></span>
                    <AppIcon name="chevron-right" :size="16" />
                  </button>
                  <div v-if="expandedLogId === entry.id" class="staff-log-entry-details">
                    <dl><div><dt>{{ t('admin.logs.requestId') }}</dt><dd>{{ entry.request_id || '—' }}</dd></div><div><dt>{{ t('logs.clientIp') }}</dt><dd>{{ entry.client_ip || '—' }}</dd></div><div><dt>{{ t('logs.queryString') }}</dt><dd>{{ entry.query_string || '—' }}</dd></div><div><dt>User-Agent</dt><dd>{{ entry.user_agent || '—' }}</dd></div><div><dt>Logger</dt><dd>{{ entry.logger || '—' }}</dd></div></dl>
                    <div class="staff-log-entry-message"><strong>Details</strong><p :class="{ 'error-text': entry.exception }">{{ entry.exception || entry.message || '—' }}</p><div v-if="entry.client_ip" class="hero-actions"><button class="small-action" type="button" @click="openIpBlockManager(entry.client_ip)">{{ t('admin.ipBlocks.blockAction') }}</button><button class="small-action" type="button" @click="openLogsForIp(entry.client_ip)">{{ t('admin.ipBlocks.viewLogs') }}</button></div></div>
                  </div>
                </article>
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
  </StaffWorkspaceShell>

  <section v-else class="admin-page" aria-labelledby="admin-locked-title">
    <div class="wire-frame page-frame admin-frame">
      <section class="wire-section admin-locked">
        <h2 id="admin-locked-title">{{ t('admin.lockedTitle') }}</h2>
        <p>{{ t('admin.lockedText') }}</p>
        <RouterLink class="button-box primary-action" to="/login">{{ t('auth.login') }}</RouterLink>
      </section>
    </div>
  </section>
</template>
