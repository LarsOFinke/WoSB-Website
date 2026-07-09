<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { FLEET_MEMBER_STATUSES, FLEET_ROLES, getFleetManagementDetail, listManageableFleets, updateFleet, updateFleetMembership } from '@/services/fleets'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { user } = useSession()
const fleets = ref([])
const selectedFleetId = ref('')
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
])

const filteredMembers = computed(() => {
  const query = memberSearch.value.trim().toLowerCase()
  return memberships.value.filter((membership) => {
    const matchesStatus = memberStatusFilter.value ? membership.status === memberStatusFilter.value : true
    const matchesRole = memberRoleFilter.value ? membership.role === memberRoleFilter.value : true
    const haystack = `${membership.user.display_name} ${membership.user.username} ${membership.note || ''}`.toLowerCase()
    return matchesStatus && matchesRole && (!query || haystack.includes(query))
  })
})

function syncForm() {
  form.description = selectedFleet.value?.description || ''
  form.standing_orders = selectedFleet.value?.standing_orders || ''
}

async function loadManageable() {
  loading.value = true
  error.value = ''
  try {
    fleets.value = await listManageableFleets()
    if (!selectedFleetId.value && fleets.value.length > 0) selectedFleetId.value = String(fleets.value[0].id)
  } catch (err) {
    error.value = err.message || t('fleets.manage.loadError')
  } finally {
    loading.value = false
  }
}

async function loadFleetDetail() {
  if (!selectedFleetId.value) {
    selectedFleet.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    selectedFleet.value = await getFleetManagementDetail(selectedFleetId.value)
    syncForm()
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

watch(selectedFleetId, async () => {
  activeTab.value = 'profile'
  memberSearch.value = ''
  memberStatusFilter.value = 'active'
  memberRoleFilter.value = ''
  await loadFleetDetail()
})

onMounted(async () => {
  await loadManageable()
  await loadFleetDetail()
})
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
          <RouterLink class="button-box" to="/fleets">{{ t('fleets.openOverview') }}</RouterLink>
          <RouterLink class="button-box" to="/profile">{{ t('common.profile') }}</RouterLink>
        </div>
      </header>

      <section class="wire-section fleet-management-panel">
        <div class="staff-filter-row fleet-command-bar">
          <label class="filter-box select-shell toolbar-select-shell">
            <span>{{ t('fleets.manage.selectFleet') }}</span>
            <select v-model="selectedFleetId">
              <option value="">{{ t('fleets.manage.noFleet') }}</option>
              <option v-for="fleet in fleets" :key="fleet.id" :value="String(fleet.id)">{{ fleet.name }}</option>
            </select>
          </label>
          <span v-if="user" class="summary-pill">{{ user.display_name }}</span>
        </div>

        <p v-if="loading" class="muted table-state">{{ t('fleets.manage.loading') }}</p>
        <p v-if="error" class="error-text table-state">{{ error }}</p>
        <p v-if="success" class="success-text table-state">{{ success }}</p>

        <div v-if="!loading && fleets.length === 0" class="empty-state">
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
                <p>{{ t(`fleets.focus.${selectedFleet.focus}`) }}</p>
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
                <h2>{{ t('fleets.manage.memberDirectory') }}</h2>
                <p>{{ t('fleets.manage.membersSubtitle') }}</p>
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

            <p v-if="filteredMembers.length === 0" class="muted table-state">{{ t('fleets.manage.noMembers') }}</p>
            <article v-for="membership in filteredMembers" :key="membership.id" class="admin-build-row fleet-member-row fleet-directory-row">
              <div class="admin-build-main">
                <strong>{{ membership.user.display_name }}</strong>
                <span>{{ membership.user.username }}</span>
                <div class="member-pill-row">
                  <span class="summary-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
                  <span class="summary-pill">{{ t(`fleets.roles.${membership.role}`) }}</span>
                </div>
                <p v-if="membership.note" class="muted member-note">{{ membership.note }}</p>
              </div>
              <div class="member-admin-controls">
                <label class="compact-select">
                  <span>{{ t('fleets.manage.role') }}</span>
                  <select :value="membership.role" @change="setMember(membership, { role: $event.target.value })">
                    <option v-for="role in FLEET_ROLES" :key="role" :value="role">{{ t(`fleets.roles.${role}`) }}</option>
                  </select>
                </label>
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
