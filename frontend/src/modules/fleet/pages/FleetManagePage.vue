<script setup>
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useFleetManagePage } from '@/modules/fleet/composables/useFleetManagePage.js'

const {
  t, user, selectedFleet, fleetRoles, activeRoleOptions, canManageRoles, activeTab, loading,
  saving, roleSaving, error, success, memberSearch, memberStatusFilter,
  memberRoleFilter, form, roleForm, memberships, pendingMembers, activeMembers,
  inactiveMembers, leadershipMembers, tabs, filteredMembers, activeDirectoryMembers,
  protectedMembers, managementFor, roleOptionsFor, roleLabel, protectionLabel, hasAnyMemberPermission,
  syncForm, resetRoleForm, editRole, loadFleetDetail, saveFleet, setMember, saveRole, removeRole, fieldPayload,
  FLEET_MEMBER_STATUSES,
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
                      <small>{{ roleLabel(leader.role) }}</small>
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
                  <span class="summary-pill">{{ roleLabel(membership.role) }}</span>
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

          <section v-else-if="activeTab === 'roles' && canManageRoles" class="fleet-role-admin-panel">
            <div class="fleet-section-heading"><div><h2>{{ t('fleets.manage.roles.title') }}</h2><p>{{ t('fleets.manage.roles.subtitle') }}</p></div></div>
            <div class="webhook-workspace-grid">
              <form class="webhook-editor" @submit.prevent="saveRole">
                <div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('fleets.manage.roles.editor') }}</span><h3>{{ roleForm.id ? t('fleets.manage.roles.edit') : t('fleets.manage.roles.create') }}</h3></div><button v-if="roleForm.id" class="small-action" type="button" @click="resetRoleForm">{{ t('common.cancel') }}</button></div>
                <label v-if="!roleForm.id" class="input-panel embedded-field"><span>{{ t('fleets.manage.roles.code') }}</span><input v-model="roleForm.code" required maxlength="40" pattern="[a-z][a-z0-9_]{1,39}" /></label>
                <label class="input-panel embedded-field"><span>{{ t('fleets.manage.roles.label') }}</span><input v-model="roleForm.label" required maxlength="80" /></label>
                <label class="input-panel embedded-field"><span>{{ t('fleets.manage.roles.rank') }}</span><input v-model.number="roleForm.rank" type="number" min="1" max="79" required /><small>{{ t('fleets.manage.roles.rankHint') }}</small></label>
                <div class="fleet-role-toggle-grid">
                  <label class="toggle-card"><span><strong>{{ t('fleets.manage.roles.leadership') }}</strong></span><input v-model="roleForm.is_leadership" type="checkbox" /></label>
                  <label class="toggle-card"><span><strong>{{ t('fleets.manage.roles.manageFleet') }}</strong></span><input v-model="roleForm.can_manage_fleet" type="checkbox" /></label>
                  <label class="toggle-card"><span><strong>{{ t('fleets.manage.roles.manageMembers') }}</strong></span><input v-model="roleForm.can_manage_members" type="checkbox" /></label>
                  <label v-if="roleForm.id" class="toggle-card"><span><strong>{{ t('fleets.manage.roles.active') }}</strong></span><input v-model="roleForm.is_active" type="checkbox" /></label>
                </div>
                <button class="form-button primary-action" type="submit" :disabled="roleSaving || roleForm.is_system">{{ roleSaving ? t('common.saving') : t('common.save') }}</button>
              </form>
              <section class="webhook-list-panel"><div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('fleets.manage.roles.catalog') }}</span><h3>{{ t('fleets.manage.roles.available') }}</h3></div><span class="summary-pill">{{ fleetRoles.length }}</span></div><div class="webhook-card-list"><article v-for="role in fleetRoles" :key="role.id" class="webhook-card" :class="{ 'is-inactive': !role.is_active }"><div class="webhook-card-main"><div class="webhook-card-title"><strong>{{ role.label }}</strong><span class="webhook-status-pill" :class="{ 'is-active': role.is_active }">{{ role.is_system ? t('fleets.manage.roles.system') : t('fleets.manage.roles.custom') }}</span></div><code>{{ role.code }}</code><p>{{ t('fleets.manage.roles.rank') }} {{ role.rank }} · {{ role.member_count }} {{ t('fleets.manage.roles.members') }}</p><div class="webhook-event-chip-row"><span v-if="role.is_leadership">{{ t('fleets.manage.roles.leadership') }}</span><span v-if="role.can_manage_fleet">{{ t('fleets.manage.roles.manageFleet') }}</span><span v-if="role.can_manage_members">{{ t('fleets.manage.roles.manageMembers') }}</span></div></div><div v-if="!role.is_system" class="webhook-card-actions"><button class="small-action" type="button" @click="editRole(role)">{{ t('admin.webhooks.actions.edit') }}</button><button class="danger-action" type="button" :disabled="role.member_count > 0" @click="removeRole(role)">{{ t('common.delete') }}</button></div></article></div></section>
            </div>
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
                  <option v-for="role in activeRoleOptions" :key="role.code" :value="role.code">{{ role.label }}</option>
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
                  <span class="summary-pill">{{ roleLabel(membership.role) }}</span>
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
                    <option v-for="role in roleOptionsFor(membership)" :key="role" :value="role">{{ roleLabel(role) }}</option>
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
