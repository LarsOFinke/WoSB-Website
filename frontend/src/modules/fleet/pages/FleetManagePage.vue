<script setup>
import { computed } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import WorkspaceStatRail from '@/core/components/WorkspaceStatRail.vue'
import FleetMemberFilters from '@/modules/fleet/components/FleetMemberFilters.vue'
import FleetMemberRow from '@/modules/fleet/components/FleetMemberRow.vue'
import { useFleetManagePage } from '@/modules/fleet/composables/useFleetManagePage.js'
import '@/styles/workspaceRefresh.css'
import '@/modules/fleet/styles/fleetManagementRefresh.css'

const {
  t, user, selectedFleet, fleetRoles, activeRoleOptions, canManageRoles, activeTab, loading,
  saving, roleSaving, error, success, memberSearch, memberStatusFilter,
  memberRoleFilter, form, roleForm, pendingMembers, activeMembers,
  inactiveMembers, leadershipMembers, tabs, filteredMembers, activeDirectoryMembers,
  protectedMembers, managementFor, roleOptionsFor, roleLabel, protectionLabel,
  resetRoleForm, editRole, saveFleet, setMember, saveRole, removeRole,
  FLEET_MEMBER_STATUSES,
} = useFleetManagePage()

const managementStats = computed(() => [
  { key: 'active', icon: 'users', label: t('fleets.manage.summary.active'), value: activeMembers.value.length },
  { key: 'pending', icon: 'inbox', label: t('fleets.manage.summary.pending'), value: pendingMembers.value.length },
  { key: 'leadership', icon: 'shield', label: t('fleets.manage.summary.leadership'), value: leadershipMembers.value.length },
  {
    key: 'directory',
    icon: 'guides',
    label: t('fleets.manage.summary.directory'),
    value: activeMembers.value.filter((member) => member.assignment || member.availability || member.preferred_ships).length,
  },
])

const visibleMembers = computed(() => activeTab.value === 'directory' ? activeDirectoryMembers.value : filteredMembers.value)
</script>

<template>
  <section class="fleet-refresh-page" aria-labelledby="fleet-manage-title">
    <div class="wire-frame page-frame fleet-refresh-frame">
      <header class="workspace-command-header fleet-refresh-header">
        <div>
          <h1 id="fleet-manage-title">{{ selectedFleet?.name || t('fleets.manage.title') }}</h1>
          <p>{{ t('fleets.manage.subtitle') }}</p>
        </div>
        <div class="workspace-command-actions">
          <RouterLink class="button-box" to="/fleet">{{ t('fleets.openOverview') }}</RouterLink>
          <RouterLink class="button-box primary-action" to="/profile">{{ t('common.profile') }}</RouterLink>
        </div>
      </header>

      <p v-if="loading" class="fleet-refresh-state muted">{{ t('fleets.manage.loading') }}</p>
      <p v-if="error" class="fleet-refresh-state error-text">{{ error }}</p>
      <p v-if="success" class="fleet-refresh-state success-text">{{ success }}</p>

      <div v-if="!loading && !selectedFleet" class="empty-state">
        <h2>{{ t('fleets.manage.lockedTitle') }}</h2>
        <p>{{ t('fleets.manage.lockedText') }}</p>
      </div>

      <template v-if="selectedFleet">
        <WorkspaceStatRail :items="managementStats" :label="t('fleets.manage.title')" />

        <section class="fleet-refresh-hierarchy" aria-labelledby="fleet-hierarchy-title">
          <div>
            <AppIcon name="shield" :size="20" />
            <p id="fleet-hierarchy-title">{{ t('fleets.manage.hierarchy.hint') }}</p>
          </div>
          <span class="summary-pill">{{ t('fleets.manage.hierarchy.protectedCount', { count: protectedMembers.length }) }}</span>
        </section>

        <nav class="fleet-refresh-tabs" role="tablist" :aria-label="t('fleets.manage.tabs.label')">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            role="tab"
            :class="{ 'is-active': activeTab === tab.key }"
            :aria-selected="activeTab === tab.key"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
            <span v-if="tab.count !== null" class="fleet-refresh-tab-count">{{ tab.count }}</span>
          </button>
        </nav>

        <main class="fleet-refresh-content">
          <form v-if="activeTab === 'profile'" class="fleet-refresh-profile-form" @submit.prevent="saveFleet">
            <div class="workspace-section-title fleet-refresh-content-heading">
              <div><h2>{{ selectedFleet.name }}</h2><p>{{ t('fleets.manage.singleFleetHint') }}</p></div>
              <span v-if="user" class="summary-pill">{{ user.display_name }}</span>
            </div>
            <section>
              <div class="workspace-section-title"><div><h3>{{ t('fleets.leadership') }}</h3></div></div>
              <p v-if="leadershipMembers.length === 0" class="muted">{{ t('fleets.noLeaders') }}</p>
              <div v-else class="fleet-refresh-leadership">
                <article v-for="leader in leadershipMembers" :key="leader.id"><strong>{{ leader.user.display_name }}</strong><small>{{ roleLabel(leader.role) }}</small></article>
              </div>
            </section>
            <label class="input-panel embedded-field"><span>{{ t('fleets.description') }}</span><textarea v-model="form.description" rows="4" maxlength="2000" /></label>
            <label class="input-panel embedded-field"><span>{{ t('fleets.standingOrders') }}</span><textarea v-model="form.standing_orders" rows="5" maxlength="3000" /></label>
            <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('common.saving') : t('fleets.manage.save') }}</button>
          </form>

          <section v-else-if="activeTab === 'requests'">
            <div class="workspace-section-title fleet-refresh-content-heading">
              <div><h2>{{ t('fleets.manage.pending') }}</h2><p>{{ t('fleets.manage.requestsSubtitle') }}</p></div>
              <span class="summary-pill">{{ pendingMembers.length }}</span>
            </div>
            <p v-if="pendingMembers.length === 0" class="muted table-state">{{ t('fleets.manage.noPending') }}</p>
            <div v-else class="fleet-refresh-member-list">
              <FleetMemberRow
                v-for="membership in pendingMembers"
                :key="membership.id"
                :membership="membership"
                :management="managementFor(membership)"
                :role-options="roleOptionsFor(membership)"
                :role-label="roleLabel"
                :protection-label="protectionLabel(membership)"
                mode="requests"
                @save="setMember(membership, $event)"
              />
            </div>
          </section>

          <section v-else-if="activeTab === 'roles' && canManageRoles">
            <div class="workspace-section-title fleet-refresh-content-heading">
              <div><h2>{{ t('fleets.manage.roles.title') }}</h2><p>{{ t('fleets.manage.roles.subtitle') }}</p></div>
              <span class="summary-pill">{{ fleetRoles.length }}</span>
            </div>
            <div class="fleet-refresh-role-layout">
              <form class="fleet-refresh-role-editor" @submit.prevent="saveRole">
                <div class="workspace-section-title">
                  <div><h3>{{ roleForm.id ? t('fleets.manage.roles.edit') : t('fleets.manage.roles.create') }}</h3></div>
                  <button v-if="roleForm.id" class="small-action" type="button" @click="resetRoleForm">{{ t('common.cancel') }}</button>
                </div>
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

              <section class="fleet-refresh-role-catalog">
                <div class="workspace-section-title"><div><h3>{{ t('fleets.manage.roles.available') }}</h3></div></div>
                <article v-for="role in fleetRoles" :key="role.id" class="fleet-refresh-role-row" :class="{ 'is-inactive': !role.is_active }">
                  <div><strong>{{ role.label }}</strong><code>{{ role.code }}</code><small>{{ t('fleets.manage.roles.rank') }} {{ role.rank }} · {{ role.member_count }} {{ t('fleets.manage.roles.members') }}</small></div>
                  <div class="fleet-refresh-role-flags"><span v-if="role.is_leadership">{{ t('fleets.manage.roles.leadership') }}</span><span v-if="role.can_manage_fleet">{{ t('fleets.manage.roles.manageFleet') }}</span><span v-if="role.can_manage_members">{{ t('fleets.manage.roles.manageMembers') }}</span></div>
                  <div v-if="!role.is_system" class="compact-actions"><button class="small-action" type="button" @click="editRole(role)">{{ t('admin.webhooks.actions.edit') }}</button><button class="danger-action" type="button" :disabled="role.member_count > 0" @click="removeRole(role)">{{ t('common.delete') }}</button></div>
                </article>
              </section>
            </div>
          </section>

          <section v-else>
            <div class="workspace-section-title fleet-refresh-content-heading">
              <div>
                <h2>{{ activeTab === 'directory' ? t('fleets.manage.extendedDirectory') : t('fleets.manage.memberDirectory') }}</h2>
                <p>{{ activeTab === 'directory' ? t('fleets.manage.directorySubtitle') : t('fleets.manage.membersSubtitle') }}</p>
              </div>
              <span class="summary-pill">{{ visibleMembers.length }}</span>
            </div>

            <FleetMemberFilters
              v-model:search="memberSearch"
              v-model:status="memberStatusFilter"
              v-model:role="memberRoleFilter"
              :statuses="FLEET_MEMBER_STATUSES"
              :roles="activeRoleOptions"
            />

            <p v-if="visibleMembers.length === 0" class="muted table-state">{{ t('fleets.manage.noMembers') }}</p>
            <template v-else>
              <div class="fleet-refresh-member-head" aria-hidden="true">
                <span>{{ t('fleets.manage.memberDirectory') }}</span>
                <span>{{ t('fleets.manage.statusFilter') }}</span>
                <span>{{ t('fleets.directory.assignment') }}</span>
                <span>{{ t('fleets.directory.discord') }}</span>
                <span aria-hidden="true"></span>
              </div>
              <div class="fleet-refresh-member-list">
                <FleetMemberRow
                  v-for="membership in visibleMembers"
                  :key="membership.id"
                  :membership="membership"
                  :management="managementFor(membership)"
                  :role-options="roleOptionsFor(membership)"
                  :role-label="roleLabel"
                  :protection-label="protectionLabel(membership)"
                  :mode="activeTab"
                  @save="setMember(membership, $event)"
                />
              </div>
            </template>
          </section>
        </main>
      </template>
    </div>
  </section>
</template>
