<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { FLEET_MEMBER_STATUSES, FLEET_ROLES, getOfficialFleetManagementDetail, updateFleet, updateFleetMembership } from '@/services/fleets'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { user } = useSession()
const selectedFleet = ref(null)
const activeTab = ref('profile')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const memberSearch = ref('')
const memberStatusFilter = ref('active')
const memberRoleFilter = ref('')

const form = reactive({ description: '', standing_orders: '' })

const memberships = computed(() => selectedFleet.value?.memberships || [])
const pendingMembers = computed(() => memberships.value.filter((row) => row.status === 'pending'))
const activeMembers = computed(() => memberships.value.filter((row) => row.status === 'active'))
const inactiveMembers = computed(() => memberships.value.filter((row) => row.status === 'inactive'))
const leadershipMembers = computed(() => activeMembers.value.filter((row) => ['fleet_admiral', 'fleet_lieutenant'].includes(row.role)))

const tabs = computed(() => [
  { key: 'profile', label: t('fleets.manage.tabs.profile'), count: null },
  { key: 'requests', label: t('fleets.manage.tabs.requests'), count: pendingMembers.value.length },
  { key: 'members', label: t('fleets.manage.tabs.members'), count: activeMembers.value.length + inactiveMembers.value.length },
  { key: 'directory', label: t('fleets.manage.tabs.directory'), count: activeMembers.value.length },
])

const filteredMembers = computed(() => {
  const query = memberSearch.value.trim().toLowerCase()
  return memberships.value.filter((membership) => {
    const matchesStatus = memberStatusFilter.value ? membership.status === memberStatusFilter.value : true
    const matchesRole = memberRoleFilter.value ? membership.role === memberRoleFilter.value : true
    const haystack = [
      membership.user.display_name,
      membership.user.username,
      membership.note,
      membership.assignment,
      membership.availability,
      membership.preferred_ships,
      membership.timezone,
      membership.discord_handle,
      membership.admin_note,
    ].filter(Boolean).join(' ').toLowerCase()
    return matchesStatus && matchesRole && (!query || haystack.includes(query))
  })
})

const activeDirectoryMembers = computed(() => filteredMembers.value.filter((membership) => membership.status === 'active'))

function syncForm() {
  form.description = selectedFleet.value?.description || ''
  form.standing_orders = selectedFleet.value?.standing_orders || ''
}

async function loadFleetDetail() {
  loading.value = true
  error.value = ''
  try {
    selectedFleet.value = await getOfficialFleetManagementDetail()
    if (selectedFleet.value) syncForm()
  } catch (err) {
    error.value = err.message || t('fleets.manage.loadError')
  } finally {
    loading.value = false
  }
}

async function saveFleet() {
  if (!selectedFleet.value) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await updateFleet(selectedFleet.value.id, {
      description: form.description,
      standing_orders: form.standing_orders,
    })
    success.value = t('fleets.manage.saved')
    await loadFleetDetail()
  } catch (err) {
    error.value = err.message || t('fleets.manage.saveError')
  } finally {
    saving.value = false
  }
}

async function setMember(membership, payload) {
  error.value = ''
  success.value = ''
  try {
    await updateFleetMembership(selectedFleet.value.id, membership.id, payload)
    success.value = t('fleets.manage.memberSaved')
    await loadFleetDetail()
  } catch (err) {
    error.value = err.message || t('fleets.manage.memberError')
  }
}

function fieldPayload(field, event) {
  return { [field]: event.target.value || null }
}

onMounted(loadFleetDetail)
</script>

<template>
  <section class="fleet-page" aria-labelledby="fleet-manage-title">
    <div class="wire-frame page-frame fleet-frame">
      <header class="wire-section page-hero fleet-hero">
        <div>
          <p class="eyebrow">{{ t('fleets.manage.eyebrow') }}</p>
          <h1 id="fleet-manage-title">{{ t('fleets.manage.title') }}</h1>
          <p>{{ t('fleets.manage.subtitle') }}</p>
        </div>
        <div class="hero-action-stack">
          <RouterLink class="button-box" to="/">{{ t('fleets.openOverview') }}</RouterLink>
          <RouterLink class="button-box" to="/profile">{{ t('common.profile') }}</RouterLink>
        </div>
      </header>

      <section class="wire-section fleet-management-panel">
        <div class="staff-filter-row fleet-command-bar">
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
          <div class="fleet-management-summary">
            <article class="summary-card compact-summary-card">
              <span>{{ t('fleets.manage.summary.active') }}</span>
              <strong>{{ activeMembers.length }}</strong>
            </article>
            <article class="summary-card compact-summary-card">
              <span>{{ t('fleets.manage.summary.pending') }}</span>
              <strong>{{ pendingMembers.length }}</strong>
            </article>
            <article class="summary-card compact-summary-card">
              <span>{{ t('fleets.manage.summary.leadership') }}</span>
              <strong>{{ leadershipMembers.length }}</strong>
            </article>
            <article class="summary-card compact-summary-card">
              <span>{{ t('fleets.manage.summary.directory') }}</span>
              <strong>{{ activeMembers.filter((member) => member.assignment || member.availability || member.preferred_ships).length }}</strong>
            </article>
          </div>

          <div class="fleet-management-tabs" role="tablist" :aria-label="t('fleets.manage.tabs.label')">
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

          <form v-if="activeTab === 'profile'" class="sectioned-form fleet-editor" @submit.prevent="saveFleet">
            <section class="form-section-card">
              <div class="form-section-heading">
                <h2>{{ selectedFleet.name }}</h2>
                <p>{{ t('fleets.manage.singleFleetHint') }}</p>
              </div>
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
                <div class="member-directory-meta">
                  <span v-if="membership.availability">{{ t('fleets.directory.availability') }}: {{ membership.availability }}</span>
                  <span v-if="membership.preferred_ships">{{ t('fleets.directory.preferredShips') }}: {{ membership.preferred_ships }}</span>
                  <span v-if="membership.timezone">{{ t('fleets.directory.timezone') }}: {{ membership.timezone }}</span>
                  <span v-if="membership.discord_handle">{{ t('fleets.directory.discord') }}: {{ membership.discord_handle }}</span>
                </div>
                <p v-if="membership.note" class="muted member-note">{{ membership.note }}</p>
              </div>
              <div class="compact-actions">
                <button class="small-action" type="button" @click="setMember(membership, { status: 'active' })">{{ t('fleets.manage.approve') }}</button>
                <button class="danger-action" type="button" @click="setMember(membership, { status: 'inactive' })">{{ t('fleets.manage.reject') }}</button>
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

              <div class="member-admin-controls extended-directory-controls">
                <label class="compact-select">
                  <span>{{ t('fleets.manage.role') }}</span>
                  <select :value="membership.role" @change="setMember(membership, { role: $event.target.value })">
                    <option v-for="role in FLEET_ROLES" :key="role" :value="role">{{ t(`fleets.roles.${role}`) }}</option>
                  </select>
                </label>
                <div class="directory-form-grid member-directory-edit-grid">
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.assignment') }}</span><input :value="membership.assignment || ''" maxlength="120" @change="setMember(membership, fieldPayload('assignment', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.availability') }}</span><input :value="membership.availability || ''" maxlength="240" @change="setMember(membership, fieldPayload('availability', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.preferredShips') }}</span><input :value="membership.preferred_ships || ''" maxlength="300" @change="setMember(membership, fieldPayload('preferred_ships', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.timezone') }}</span><input :value="membership.timezone || ''" maxlength="80" @change="setMember(membership, fieldPayload('timezone', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.discord') }}</span><input :value="membership.discord_handle || ''" maxlength="120" @change="setMember(membership, fieldPayload('discord_handle', $event))" /></label>
                  <label class="input-panel embedded-field compact-directory-field"><span>{{ t('fleets.directory.adminNote') }}</span><input :value="membership.admin_note || ''" maxlength="1200" @change="setMember(membership, fieldPayload('admin_note', $event))" /></label>
                </div>
                <div class="compact-actions">
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
