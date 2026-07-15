<script setup>
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useFleetManagePage } from '@/modules/fleet/composables/useFleetManagePage.js'

const {
  t, user, selectedFleet, activeTab, loading,
  saving, error, success, memberSearch, memberStatusFilter,
  memberRoleFilter, form, memberships, pendingMembers, activeMembers,
  inactiveMembers, leadershipMembers, tabs, filteredMembers, activeDirectoryMembers,
  protectedMembers, managementFor, roleOptionsFor, protectionLabel, hasAnyMemberPermission,
  syncForm, loadFleetDetail, saveFleet, setMember, fieldPayload,
  FLEET_MEMBER_STATUSES, FLEET_ROLES,
} = useFleetManagePage()
</script>

<template>
  <section class="fleet-page" aria-labelledby="fleet-manage-title">
    <div class="wire-frame page-frame fleet-frame">
      <PageHeader
        :eyebrow="t('fleets.manage.eyebrow')"
        :title="t('fleets.manage.title')"
        :description="t('fleets.manage.subtitle')"
        title-id="fleet-manage-title"
      >
        <template #meta>
          <span v-if="selectedFleet" class="summary-pill">{{ selectedFleet.name }}</span>
          <span v-if="user" class="summary-pill">{{ user.display_name }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/">{{ t('fleets.openOverview') }}</RouterLink>
          <RouterLink class="button-box primary-action" to="/profile">{{ t('common.profile') }}</RouterLink>
        </template>
      </PageHeader>

      <section class="wire-section fleet-management-panel fleet-command-workspace">
        <div class="fleet-command-bar polished-command-bar">
          <div>
            <p class="eyebrow">{{ t('fleets.manage.commandScope') }}</p>
            <h2>{{ selectedFleet?.name || t('fleets.manage.noFleet') }}</h2>
          </div>
          <span v-if="user" class="summary-pill">{{ user.display_name }}</span>
        </div>

        <p v-if="loading" class="muted table-state">{{ t('fleets.manage.loading') }}</p>
        <p v-if="error" class="error-text table-state">{{ error }}</p>
        <p v-if="success" class="success-text table-state">{{ success }}</p>

        <div v-if="!loading && !selectedFleet" class="empty-state">
          <h2>{{ t('fleets.manage.lockedTitle') }}</h2>
          <p>{{ t('fleets.manage.lockedText') }}</p>
        </div>

        <template v-if="selectedFleet">
          <div class="workspace-metric-grid fleet-management-summary">
            <MetricCard :label="t('fleets.manage.summary.active')" :value="activeMembers.length" tone="accent" />
            <MetricCard :label="t('fleets.manage.summary.pending')" :value="pendingMembers.length" />
            <MetricCard :label="t('fleets.manage.summary.leadership')" :value="leadershipMembers.length" />
            <MetricCard :label="t('fleets.manage.summary.directory')" :value="activeMembers.filter((member) => member.assignment || member.availability || member.preferred_ships).length" />
          </div>

          <section class="fleet-hierarchy-policy" aria-labelledby="fleet-hierarchy-title">
            <div class="fleet-hierarchy-policy-head">
              <div>
                <p class="eyebrow">{{ t('fleets.manage.hierarchy.eyebrow') }}</p>
                <h2 id="fleet-hierarchy-title">{{ t('fleets.manage.hierarchy.title') }}</h2>
                <p>{{ t('fleets.manage.hierarchy.hint') }}</p>
              </div>
              <span class="summary-pill fleet-protection-summary">{{ t('fleets.manage.hierarchy.protectedCount', { count: protectedMembers.length }) }}</span>
            </div>
            <div class="fleet-hierarchy-levels">
              <article><span>01</span><strong>{{ t('fleets.manage.hierarchy.adminTitle') }}</strong><small>{{ t('fleets.manage.hierarchy.adminHint') }}</small></article>
              <article><span>02</span><strong>{{ t('fleets.manage.hierarchy.commandTitle') }}</strong><small>{{ t('fleets.manage.hierarchy.commandHint') }}</small></article>
              <article><span>03</span><strong>{{ t('fleets.manage.hierarchy.lieutenantTitle') }}</strong><small>{{ t('fleets.manage.hierarchy.lieutenantHint') }}</small></article>
            </div>
          </section>

          <div class="fleet-management-tabs workspace-tab-rail" role="tablist" :aria-label="t('fleets.manage.tabs.label')">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="tab-button fleet-tab-button"
              :class="{ 'is-active': activeTab === tab.key }"
              type="button"
              role="tab"
              :aria-selected="activeTab === tab.key"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span v-if="tab.count !== null" class="tab-count">{{ tab.count }}</span>
            </button>
          </div>

          <form v-if="activeTab === 'profile'" class="sectioned-form fleet-editor fleet-profile-editor" @submit.prevent="saveFleet">
            <section class="form-section-card">
              <div class="form-section-heading">
                <h2>{{ selectedFleet.name }}</h2>
                <p>{{ t('fleets.manage.singleFleetHint') }}</p>
              </div>
              <section class="fleet-leadership-block">
                <div class="fleet-section-heading"><div><h3>{{ t('fleets.leadership') }}</h3></div></div>
                <p v-if="leadershipMembers.length === 0" class="muted">{{ t('fleets.noLeaders') }}</p>
                <div v-else class="fleet-leadership-grid">
                  <article v-for="leader in leadershipMembers" :key="leader.id" class="fleet-leader-card">
                    <div>
                      <strong>{{ leader.user.display_name }}</strong>
                      <small>{{ t(`fleets.roles.${leader.role}`) }}</small>
                    </div>
                  </article>
                </div>
              </section>
              <label class="input-panel embedded-field"><span>{{ t('fleets.description') }}</span><textarea v-model="form.description" rows="4" maxlength="2000" /></label>
              <label class="input-panel embedded-field"><span>{{ t('fleets.standingOrders') }}</span><textarea v-model="form.standing_orders" rows="5" maxlength="3000" /></label>
              <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('common.saving') : t('fleets.manage.save') }}</button>
            </section>
          </form>

          <section v-else-if="activeTab === 'requests'" class="fleet-member-board fleet-request-board">
            <div class="fleet-section-heading">
              <div>
                <h2>{{ t('fleets.manage.pending') }}</h2>
                <p>{{ t('fleets.manage.requestsSubtitle') }}</p>
              </div>
            </div>
            <p v-if="pendingMembers.length === 0" class="muted table-state">{{ t('fleets.manage.noPending') }}</p>
            <article v-for="membership in pendingMembers" :key="membership.id" class="admin-build-row fleet-member-row fleet-request-row">
              <div class="admin-build-main">
                <strong>{{ membership.user.display_name }}</strong>
                <span>{{ membership.user.username }}</span>
                <div class="member-pill-row">
                  <span class="summary-pill">{{ t(`roles.${membership.user.role}`) }}</span>
                  <span class="summary-pill">{{ t(`fleets.roles.${membership.role}`) }}</span>
                  <span v-if="managementFor(membership).protected" class="summary-pill fleet-protected-pill">{{ t('fleets.manage.protectedRole') }}</span>
                </div>
                <div class="member-directory-meta">
                  <span v-if="membership.availability">{{ t('fleets.directory.availability') }}: {{ membership.availability }}</span>
                  <span v-if="membership.preferred_ships">{{ t('fleets.directory.preferredShips') }}: {{ membership.preferred_ships }}</span>
                  <span v-if="membership.timezone">{{ t('fleets.directory.timezone') }}: {{ membership.timezone }}</span>
                  <span v-if="membership.discord_handle">{{ t('fleets.directory.discord') }}: {{ membership.discord_handle }}</span>
                </div>
                <p v-if="membership.note" class="muted member-note">{{ membership.note }}</p>
              </div>
              <div class="fleet-request-actions">
                <div v-if="managementFor(membership).reason" class="fleet-protection-notice">
                  <strong>{{ t('fleets.manage.protectedRole') }}</strong>
                  <small>{{ protectionLabel(membership) }}</small>
                </div>
                <div v-if="managementFor(membership).can_change_status" class="compact-actions">
                  <button class="small-action" type="button" @click="setMember(membership, { status: 'active' })">{{ t('fleets.manage.approve') }}</button>
                  <button class="danger-action" type="button" @click="setMember(membership, { status: 'inactive' })">{{ t('fleets.manage.reject') }}</button>
                </div>
              </div>
            </article>
          </section>

          <section v-else class="fleet-member-directory">
            <div class="fleet-section-heading">
              <div>
                <h2>{{ activeTab === 'directory' ? t('fleets.manage.extendedDirectory') : t('fleets.manage.memberDirectory') }}</h2>
                <p>{{ activeTab === 'directory' ? t('fleets.manage.directorySubtitle') : t('fleets.manage.membersSubtitle') }}</p>
              </div>
            </div>

            <div class="wire-section filter-panel fleet-member-filters">
              <label class="filter-box search-shell">
                <span>{{ t('fleets.manage.memberSearch') }}</span>
                <input v-model="memberSearch" type="search" :placeholder="t('fleets.manage.memberSearchPlaceholder')" />
              </label>
              <label class="filter-box select-shell toolbar-select-shell">
                <span>{{ t('fleets.manage.statusFilter') }}</span>
                <select v-model="memberStatusFilter">
                  <option value="">{{ t('fleets.manage.allStatuses') }}</option>
                  <option v-for="status in FLEET_MEMBER_STATUSES" :key="status" :value="status">{{ t(`fleets.status.${status}`) }}</option>
                </select>
              </label>
              <label class="filter-box select-shell toolbar-select-shell">
                <span>{{ t('fleets.manage.roleFilter') }}</span>
                <select v-model="memberRoleFilter">
                  <option value="">{{ t('fleets.manage.allRoles') }}</option>
                  <option v-for="role in FLEET_ROLES" :key="role" :value="role">{{ t(`fleets.roles.${role}`) }}</option>
                </select>
              </label>
            </div>

            <p v-if="(activeTab === 'directory' ? activeDirectoryMembers : filteredMembers).length === 0" class="muted table-state">{{ t('fleets.manage.noMembers') }}</p>
            <article v-for="membership in (activeTab === 'directory' ? activeDirectoryMembers : filteredMembers)" :key="membership.id" class="admin-build-row fleet-member-row fleet-directory-row extended-member-row">
              <div class="admin-build-main">
                <strong>{{ membership.user.display_name }}</strong>
                <span>{{ membership.user.username }}</span>
                <div class="member-pill-row">
                  <span class="summary-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
                  <span class="summary-pill">{{ t(`fleets.roles.${membership.role}`) }}</span>
                  <span v-if="membership.user.role !== 'user'" class="summary-pill fleet-site-role-pill">{{ t(`roles.${membership.user.role}`) }}</span>
                  <span v-if="managementFor(membership).protected" class="summary-pill fleet-protected-pill">{{ t('fleets.manage.protectedRole') }}</span>
                  <span v-if="membership.assignment" class="summary-pill">{{ membership.assignment }}</span>
                </div>
                <div class="member-directory-meta">
                  <span v-if="membership.availability">{{ t('fleets.directory.availability') }}: {{ membership.availability }}</span>
                  <span v-if="membership.preferred_ships">{{ t('fleets.directory.preferredShips') }}: {{ membership.preferred_ships }}</span>
                  <span v-if="membership.timezone">{{ t('fleets.directory.timezone') }}: {{ membership.timezone }}</span>
                  <span v-if="membership.discord_handle">{{ t('fleets.directory.discord') }}: {{ membership.discord_handle }}</span>
                </div>
                <p v-if="membership.note" class="muted member-note">{{ membership.note }}</p>
                <p v-if="membership.admin_note" class="muted member-note internal-note">{{ t('fleets.directory.adminNote') }}: {{ membership.admin_note }}</p>
              </div>

              <div class="member-admin-controls extended-directory-controls" :class="{ 'is-read-only': !hasAnyMemberPermission(membership) }">
                <div v-if="managementFor(membership).reason" class="fleet-protection-notice">
                  <strong>{{ t('fleets.manage.protectedRole') }}</strong>
                  <small>{{ protectionLabel(membership) }}</small>
                </div>
                <label v-if="managementFor(membership).can_change_role" class="compact-select">
                  <span>{{ t('fleets.manage.role') }}</span>
                  <select :value="membership.role" @change="setMember(membership, { role: $event.target.value })">
                    <option v-for="role in roleOptionsFor(membership)" :key="role" :value="role">{{ t(`fleets.roles.${role}`) }}</option>
                  </select>
                </label>
                <div v-if="managementFor(membership).can_edit_directory" class="directory-form-grid member-directory-edit-grid">
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.assignment') }}</span><input :value="membership.assignment || ''" maxlength="120" @change="setMember(membership, fieldPayload('assignment', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.adminNote') }}</span><input :value="membership.admin_note || ''" maxlength="1200" @change="setMember(membership, fieldPayload('admin_note', $event))" /></label>
                </div>
                <div v-if="managementFor(membership).can_change_status" class="compact-actions">
                  <button v-if="membership.status !== 'active'" class="small-action" type="button" @click="setMember(membership, { status: 'active' })">{{ t('fleets.manage.activate') }}</button>
                  <button v-if="membership.status !== 'inactive'" class="danger-action" type="button" @click="setMember(membership, { status: 'inactive' })">{{ t('fleets.manage.deactivate') }}</button>
                </div>
              </div>
            </article>
          </section>
        </template>
      </section>
    </div>
  </section>
</template>
