<script setup>
import { computed } from 'vue'

import MetricCard from '@/core/components/MetricCard.vue'
import AuditLogPanel from '@/modules/admin/components/AuditLogPanel.vue'
import IpBlockManagementPanel from '@/modules/admin/components/IpBlockManagementPanel.vue'
import StaffOverviewPanel from '@/modules/admin/components/StaffOverviewPanel.vue'
import StaffFilterSurface from '@/modules/admin/components/StaffFilterSurface.vue'
import SystemLogPanel from '@/modules/admin/components/SystemLogPanel.vue'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import SystemOperationsPanel from '@/modules/admin/components/SystemOperationsPanel.vue'
import { useAdminWorkspace } from '@/modules/admin/composables/useAdminWorkspace'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const {
  locale, t, isAdmin, isStaff, user, activeTab,
  builds, buildRoles, roleDrafts, newBuildRole, pendingRoleDelete, users, fleetEvents, forumThreads, guides, groups, registrationRequests,
  ipBlockPrefill, logSummary, ipBlockOverview, overviewLoading, logsWorkspace,
  search, contentSearch, calendarCategory, registrationStatus, registrationSearch,
  registrationFromDate, registrationToDate, calendarSearch, calendarFromDate, calendarToDate,
  contentScope, contentOwner, buildType, buildRate, buildVisibility, userSearch, userRole,
  userStatus,
  loading, roleBusy, roleMessage, userLoading, calendarLoading, contentLoading, registrationLoading,
  error, userError, calendarError, contentError, registrationError, moderatorSuccess,
  pendingDelete, registrationDecisionNotes, apiStatus, apiStatusDetail, moderatorForm,
  filteredBuilds, filteredUsers, filteredEvents, upcomingEvents, visibleForumThreads, visibleGuides,
  visibleGroups, visibleContentCount, pendingRegistrationRows, oldestPendingRequest,
  nextOverviewEvent, buildRates, buildCountLabel, userCountLabel, eventCountLabel,
  contentCountLabel, registrationCountLabel, categoryOptions,
  crewTotal, formatDateTime, formatEventRange, clearConfirmation, isPending, askDelete,
  loadBuilds, loadUsers, loadStatus, loadAdminOverviewMetrics, loadOverview, loadRegistrations,
  approveRegistration, rejectRegistration, openIpBlockManager, loadCalendar,
  loadContent, confirmDeleteBuild, submitBuildRole, saveBuildRole, askDeleteBuildRole, cancelDeleteBuildRole, removeBuildRole, changeBuildRole, confirmDeleteEvent, confirmDeleteThread, confirmDeleteGuide,
  confirmCloseGroup, submitModerator, changeUserRole, toggleUserActive, canManageUser,
  navigateToTab, resetRegistrationFilters, resetCalendarFilters, resetContentFilters,
  resetBuildFilters, resetUserFilters, canAccessTab,
} = useAdminWorkspace()

const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))

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
            <MetricCard :label="t('admin.security.events')" :value="logSummary.total_events" :hint="t('admin.logs.dashboardHint')" />
            <MetricCard :label="t('admin.security.elevatedCandidates')" :value="(logSummary.threat_counts?.elevated || 0) + (logSummary.threat_counts?.critical || 0)" :hint="t('admin.logs.errorHint')" tone="danger" />
            <MetricCard :label="t('admin.security.uniqueIps')" :value="logSummary.unique_ips" :hint="t('admin.logs.slowHint')" />
            <MetricCard :label="t('admin.workspace.cards.ipBlocks')" :value="ipBlockOverview.active" :hint="t('admin.workspace.cards.ipBlocksHint')" />
          </div>
        </section>

        <section v-if="activeTab === 'registrations' && isStaff" class="wire-section admin-panel staff-management-panel">
          <div class="admin-panel-heading">
            <div><h2>{{ t('admin.registrations.title') }}</h2><p>{{ t('admin.registrations.subtitle') }}</p></div>
            <span class="summary-pill">{{ registrationCountLabel }}</span>
          </div>
          <StaffFilterSurface
            :title="t('admin.workspace.filters.title')"
            :hint="t('admin.workspace.filters.registrationHint')"
            :reset-label="t('admin.workspace.filters.reset')"
            @reset="resetRegistrationFilters"
          >
            <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="registrationStatus"><option value="pending">{{ t('admin.registrations.status.pending') }}</option><option value="approved">{{ t('admin.registrations.status.approved') }}</option><option value="rejected">{{ t('admin.registrations.status.rejected') }}</option><option value="">{{ t('admin.registrations.status.all') }}</option></select></label>
              <label class="filter-box admin-search"><input v-model="registrationSearch" type="search" :placeholder="t('admin.workspace.filters.registrationSearch')" /></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.from') }}</span><input v-model="registrationFromDate" type="date" /></label>
              <label class="filter-box staff-date-filter"><span>{{ t('admin.security.to') }}</span><input v-model="registrationToDate" type="date" /></label>
          </StaffFilterSurface>
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

        <section v-if="activeTab === 'logs' && isAdmin" class="wire-section admin-panel staff-management-panel system-log-admin-panel">
          <SystemLogPanel :workspace="logsWorkspace" @block-ip="openIpBlockManager" />
        </section>

        <section v-if="activeTab === 'ip-blocks' && isAdmin" class="wire-section admin-panel staff-management-panel ip-block-admin-panel">
          <IpBlockManagementPanel
            :initial-ip="ipBlockPrefill"
            :can-manage="isAdmin"
            @consumed-initial-ip="ipBlockPrefill = ''"
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
          <StaffFilterSurface
            :title="t('admin.workspace.filters.title')"
            :hint="t('admin.workspace.filters.calendarHint')"
            :reset-label="t('admin.workspace.filters.reset')"
            @reset="resetCalendarFilters"
          >
            <template #actions>
              <div class="hero-actions">
                <RouterLink class="small-action" to="/calendar">{{ t('admin.calendar.openCalendar') }}</RouterLink>
                <button class="small-action" type="button" @click="resetCalendarFilters">{{ t('admin.workspace.filters.reset') }}</button>
              </div>
            </template>
            <label class="filter-box admin-search"><input v-model="calendarSearch" type="search" :placeholder="t('admin.workspace.filters.calendarSearch')" /></label>
            <label class="filter-box type-filter-box select-shell toolbar-select-shell"><select v-model="calendarCategory"><option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
            <label class="filter-box staff-date-filter"><span>{{ t('admin.security.from') }}</span><input v-model="calendarFromDate" type="date" /></label>
            <label class="filter-box staff-date-filter"><span>{{ t('admin.security.to') }}</span><input v-model="calendarToDate" type="date" /></label>
          </StaffFilterSurface>
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
          <StaffFilterSurface
            :title="t('admin.workspace.filters.title')"
            :hint="t('admin.workspace.filters.contentHint')"
            :reset-label="t('admin.workspace.filters.reset')"
            @reset="resetContentFilters"
          >
            <label class="filter-box admin-search"><input v-model="contentSearch" type="search" :placeholder="t('admin.content.searchPlaceholder')" /></label>
              <label class="filter-box select-shell"><select v-model="contentScope"><option value="all">{{ t('admin.workspace.filters.allContent') }}</option><option value="forum">{{ t('admin.content.forum') }}</option><option value="guides">{{ t('admin.content.guides') }}</option><option value="groups">{{ t('admin.content.announcements') }}</option></select></label>
              <label class="filter-box admin-search"><input v-model="contentOwner" type="search" :placeholder="t('admin.workspace.filters.ownerSearch')" /></label>
          </StaffFilterSurface>
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

          <section class="staff-build-role-manager" aria-labelledby="staff-build-roles-title">
            <div class="staff-build-role-heading">
              <div><h3 id="staff-build-roles-title">{{ t('admin.buildRoles.title') }}</h3><p>{{ t('admin.buildRoles.subtitle') }}</p></div>
            </div>
            <form class="staff-build-role-create" @submit.prevent="submitBuildRole">
              <label><span>{{ t('admin.buildRoles.slug') }}</span><input v-model="newBuildRole.slug" required maxlength="32" pattern="[a-z0-9][a-z0-9_-]{0,31}" /></label>
              <label><span>{{ t('admin.buildRoles.label') }}</span><input v-model="newBuildRole.label" required maxlength="80" /></label>
              <label class="is-wide"><span>{{ t('admin.buildRoles.description') }}</span><input v-model="newBuildRole.description" maxlength="500" /></label>
              <label><span>{{ t('admin.buildRoles.sortOrder') }}</span><input v-model.number="newBuildRole.sort_order" type="number" min="-10000" max="10000" /></label>
              <button class="small-action primary-action" type="submit" :disabled="roleBusy === 'create'">{{ t('admin.buildRoles.create') }}</button>
            </form>
            <p v-if="roleMessage" class="success-text table-state" role="status">{{ roleMessage }}</p>
            <div class="staff-build-role-list">
              <article v-for="role in buildRoles" :key="role.slug" class="staff-build-role-row">
                <code>{{ role.slug }}</code>
                <label><span>{{ t('admin.buildRoles.label') }}</span><input v-model="roleDrafts[role.slug].label" maxlength="80" /></label>
                <label class="is-wide"><span>{{ t('admin.buildRoles.description') }}</span><input v-model="roleDrafts[role.slug].description" maxlength="500" /></label>
                <label><span>{{ t('admin.buildRoles.sortOrder') }}</span><input v-model.number="roleDrafts[role.slug].sort_order" type="number" min="-10000" max="10000" /></label>
                <div v-if="pendingRoleDelete === role.slug" class="delete-confirmation compact-actions">
                  <span>{{ t('admin.buildRoles.confirmDelete') }}</span>
                  <button class="danger-action" type="button" :disabled="roleBusy === `delete:${role.slug}`" @click="removeBuildRole(role.slug)">{{ t('admin.buildRoles.deleteNow') }}</button>
                  <button class="small-action" type="button" @click="cancelDeleteBuildRole">{{ t('common.cancel') }}</button>
                </div>
                <div v-else class="compact-actions">
                  <button class="small-action" type="button" :disabled="roleBusy === `save:${role.slug}`" @click="saveBuildRole(role.slug)">{{ t('admin.buildRoles.save') }}</button>
                  <button class="danger-action" type="button" @click="askDeleteBuildRole(role.slug)">{{ t('admin.buildRoles.delete') }}</button>
                </div>
              </article>
            </div>
          </section>

          <StaffFilterSurface
            :title="t('admin.workspace.filters.title')"
            :hint="t('admin.workspace.filters.buildHint')"
            :reset-label="t('admin.workspace.filters.reset')"
            @reset="resetBuildFilters"
          >
            <label class="filter-box admin-search"><input v-model="search" type="search" :placeholder="t('admin.builds.searchPlaceholder')" /></label>
            <label class="filter-box select-shell"><select v-model="buildType"><option value="">{{ t('admin.workspace.filters.allBuildTypes') }}</option><option v-for="role in buildRoles" :key="role.slug" :value="role.slug">{{ role.label }}</option></select></label>
            <label class="filter-box select-shell"><select v-model="buildRate"><option value="">{{ t('admin.workspace.filters.allRates') }}</option><option v-for="rate in buildRates" :key="rate" :value="String(rate)">{{ t('common.rate') }} {{ rate }}</option></select></label>
            <label class="filter-box select-shell"><select v-model="buildVisibility"><option value="">{{ t('admin.workspace.filters.allSources') }}</option><option value="official">{{ t('admin.workspace.filters.officialBuilds') }}</option><option value="community">{{ t('admin.workspace.filters.communityBuilds') }}</option></select></label>
          </StaffFilterSurface>
          <p v-if="loading" class="muted table-state">{{ t('admin.builds.loading') }}</p><p v-else-if="error" class="error-text table-state">{{ error }}</p><p v-else-if="filteredBuilds.length === 0" class="muted table-state">{{ t('admin.builds.empty') }}</p>
          <div v-else class="admin-build-list">
            <article v-for="build in filteredBuilds" :key="build.id" class="admin-build-row staff-build-role-assignment">
              <div class="admin-build-main"><strong>{{ build.build_name }}</strong><span>{{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ build.build_role_label }} · ▲ {{ build.upvote_count || 0 }} · {{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}</span><small v-if="build.is_official_template" class="summary-pill staff-inline-pill">{{ t('admin.workspace.filters.officialBuilds') }}</small></div>
              <label class="staff-build-role-select"><span>{{ t('admin.buildRoles.assign') }}</span><select :value="build.build_type" :disabled="roleBusy === `assign:${build.id}`" @change="changeBuildRole(build, $event)"><option v-for="role in buildRoles" :key="role.slug" :value="role.slug">{{ role.label }}</option></select></label>
              <div v-if="isPending('build', build.id)" class="delete-confirmation"><span>{{ t('admin.builds.confirmDelete') }}</span><button class="danger-action" type="button" @click="confirmDeleteBuild(build.id)">{{ t('admin.builds.deleteNow') }}</button><button class="small-action" type="button" @click="clearConfirmation">{{ t('common.cancel') }}</button></div><button v-else class="danger-action" type="button" @click="askDelete('build', build.id)">{{ t('admin.builds.delete') }}</button>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'users' && isAdmin" class="wire-section admin-panel admin-users-panel">
          <div class="admin-panel-heading"><div><h2>{{ t('admin.users.title') }}</h2><p>{{ t('admin.users.subtitle') }}</p></div><span class="summary-pill">{{ userCountLabel }}</span></div>
          <form class="moderator-form" @submit.prevent="submitModerator"><label class="input-panel embedded-field"><span>{{ t('auth.username') }}</span><input v-model="moderatorForm.username" required minlength="3" maxlength="80" /></label><label class="input-panel embedded-field"><span>{{ t('profile.displayName') }}</span><input v-model="moderatorForm.display_name" required maxlength="120" /></label><label class="input-panel embedded-field"><span>{{ t('auth.password') }}</span><input v-model="moderatorForm.password" type="password" required minlength="12" /></label><button class="form-button primary-action" type="submit">{{ t('admin.users.createModerator') }}</button></form>
          <StaffFilterSurface
            :title="t('admin.workspace.filters.title')"
            :hint="t('admin.workspace.filters.userHint')"
            :reset-label="t('admin.workspace.filters.reset')"
            @reset="resetUserFilters"
          >
            <label class="filter-box admin-search"><input v-model="userSearch" type="search" :placeholder="t('admin.workspace.filters.userSearch')" /></label>
              <label class="filter-box select-shell"><select v-model="userRole"><option value="">{{ t('admin.workspace.filters.allRoles') }}</option><option value="admin">{{ t('roles.admin') }}</option><option value="moderator">{{ t('roles.moderator') }}</option><option value="user">{{ t('roles.user') }}</option></select></label>
              <label class="filter-box select-shell"><select v-model="userStatus"><option value="">{{ t('admin.workspace.filters.allStatuses') }}</option><option value="active">{{ t('fleets.status.active') }}</option><option value="inactive">{{ t('fleets.status.inactive') }}</option></select></label>
          </StaffFilterSurface>
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
