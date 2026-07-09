<script setup>
import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { joinFleet, listFleets, listMyFleetMemberships } from '@/services/fleets'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()
const fleets = ref([])
const myMemberships = ref([])
const loading = ref(false)
const applying = ref(false)
const error = ref('')
const applicationError = ref('')
const applicationSuccess = ref('')
const focusFilter = ref('')
const applyingFleetId = ref('')
const applicationNote = ref('')

const filteredFleets = computed(() => focusFilter.value ? fleets.value.filter((fleet) => fleet.focus === focusFilter.value) : fleets.value)
const focusOptions = computed(() => [...new Set(fleets.value.map((fleet) => fleet.focus))])
const membershipByFleet = computed(() => Object.fromEntries(myMemberships.value.map((membership) => [membership.fleet_id, membership])))
const hasMemberships = computed(() => myMemberships.value.length > 0)
const activeApplications = computed(() => myMemberships.value.filter((membership) => ['active', 'pending'].includes(membership.status)))

function membershipFor(fleet) {
  return membershipByFleet.value[fleet.id] || null
}

function openApplication(fleet) {
  applicationError.value = ''
  applicationSuccess.value = ''
  applyingFleetId.value = String(fleet.id)
  applicationNote.value = membershipFor(fleet)?.note || ''
}

function closeApplication() {
  applyingFleetId.value = ''
  applicationNote.value = ''
}

async function loadMemberships() {
  if (!isAuthenticated.value) {
    myMemberships.value = []
    return
  }
  try {
    myMemberships.value = await listMyFleetMemberships()
  } catch {
    myMemberships.value = []
  }
}

async function loadFleets() {
  loading.value = true
  error.value = ''
  try {
    fleets.value = await listFleets()
    await loadMemberships()
  } catch (err) {
    error.value = err.message || t('fleets.loadError')
  } finally {
    loading.value = false
  }
}

async function submitApplication(fleet) {
  applying.value = true
  applicationError.value = ''
  applicationSuccess.value = ''
  try {
    await joinFleet({ fleet_id: fleet.id, note: applicationNote.value || null })
    applicationSuccess.value = t('fleets.application.sent', { fleet: fleet.name })
    closeApplication()
    await loadFleets()
  } catch (err) {
    applicationError.value = err.message || t('fleets.application.error')
  } finally {
    applying.value = false
  }
}

onMounted(loadFleets)
</script>

<template>
  <section class="fleet-page" aria-labelledby="fleet-title">
    <div class="wire-frame page-frame fleet-frame">
      <header class="wire-section page-hero fleet-hero">
        <div>
          <p class="eyebrow">{{ t('fleets.eyebrow') }}</p>
          <h1 id="fleet-title">{{ t('fleets.title') }}</h1>
          <p>{{ t('fleets.subtitle') }}</p>
        </div>
        <div class="hero-action-stack">
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/fleets/manage">{{ t('fleets.manageCta') }}</RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/register">{{ t('fleets.registerCta') }}</RouterLink>
          <RouterLink v-if="isAuthenticated && hasMemberships" class="button-box" to="/profile">{{ t('fleets.profileCta') }}</RouterLink>
        </div>
      </header>

      <section class="wire-section filter-panel fleet-filter-panel">
        <div>
          <p class="eyebrow">{{ t('fleets.filterEyebrow') }}</p>
          <h2>{{ t('fleets.filterTitle') }}</h2>
        </div>
        <label class="filter-box select-shell toolbar-select-shell">
          <span>{{ t('fleets.focusFilter') }}</span>
          <select v-model="focusFilter">
            <option value="">{{ t('fleets.allFleets') }}</option>
            <option v-for="focus in focusOptions" :key="focus" :value="focus">{{ t(`fleets.focus.${focus}`) }}</option>
          </select>
        </label>
      </section>

      <section v-if="isAuthenticated && activeApplications.length" class="wire-section fleet-application-strip">
        <div>
          <p class="eyebrow">{{ t('fleets.application.myStatus') }}</p>
          <h2>{{ t('fleets.application.myFleets') }}</h2>
        </div>
        <div class="application-status-list">
          <span v-for="membership in activeApplications" :key="membership.id" class="summary-pill">
            {{ membership.fleet.name }} · {{ t(`fleets.status.${membership.status}`) }}
          </span>
        </div>
      </section>

      <p v-if="loading" class="muted table-state">{{ t('fleets.loading') }}</p>
      <p v-else-if="error" class="error-text table-state">{{ error }}</p>
      <p v-if="applicationError" class="error-text table-state">{{ applicationError }}</p>
      <p v-if="applicationSuccess" class="success-text table-state">{{ applicationSuccess }}</p>

      <section v-if="!loading && !error" class="fleet-card-grid">
        <article v-for="fleet in filteredFleets" :key="fleet.id" class="wire-section fleet-card fleet-application-card">
          <div class="fleet-card-header">
            <span class="summary-pill">{{ t(`fleets.focus.${fleet.focus}`) }}</span>
            <span class="muted">{{ t('fleets.memberSummary', { active: fleet.active_members_count, pending: fleet.pending_members_count }) }}</span>
          </div>
          <h2>{{ fleet.name }}</h2>
          <p>{{ fleet.description || t('fleets.noDescription') }}</p>
          <div class="fleet-leaders">
            <strong>{{ t('fleets.leadership') }}</strong>
            <span v-if="fleet.leaders.length === 0" class="muted">{{ t('fleets.noLeaders') }}</span>
            <span v-for="leader in fleet.leaders" :key="leader.id" class="summary-pill">{{ leader.user.display_name }} · {{ t(`fleets.roles.${leader.role}`) }}</span>
          </div>

          <div class="fleet-application-actions">
            <template v-if="isAuthenticated">
              <span v-if="membershipFor(fleet)" class="summary-pill fleet-status-pill">
                {{ t(`fleets.status.${membershipFor(fleet).status}`) }} · {{ t(`fleets.roles.${membershipFor(fleet).role}`) }}
              </span>
              <button
                v-if="!membershipFor(fleet) || membershipFor(fleet).status === 'inactive'"
                class="form-button"
                type="button"
                @click="openApplication(fleet)"
              >
                {{ membershipFor(fleet)?.status === 'inactive' ? t('fleets.application.reapply') : t('fleets.application.apply') }}
              </button>
            </template>
            <RouterLink v-else class="button-box" to="/login">{{ t('fleets.application.loginToApply') }}</RouterLink>
          </div>

          <form v-if="applyingFleetId === String(fleet.id)" class="fleet-inline-application" @submit.prevent="submitApplication(fleet)">
            <label class="input-panel embedded-field">
              <span>{{ t('fleets.application.noteLabel') }}</span>
              <textarea v-model="applicationNote" rows="4" maxlength="1000" :placeholder="t('fleets.application.notePlaceholder')" />
            </label>
            <div class="form-actions compact-actions">
              <button class="form-button primary-action" type="submit" :disabled="applying">
                {{ applying ? t('common.saving') : t('fleets.application.submit') }}
              </button>
              <button class="form-button secondary-action" type="button" @click="closeApplication">{{ t('common.cancel') }}</button>
            </div>
          </form>
        </article>
      </section>
    </div>
  </section>
</template>
