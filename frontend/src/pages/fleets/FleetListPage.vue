<script setup>
import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getOfficialFleet, joinFleet, listMyFleetMemberships } from '@/services/fleets'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()
const fleet = ref(null)
const myMemberships = ref([])
const loading = ref(false)
const applying = ref(false)
const error = ref('')
const applicationError = ref('')
const applicationSuccess = ref('')
const applicationOpen = ref(false)
const applicationNote = ref('')
const applicationDetails = ref({ availability: '', preferred_ships: '', timezone: '', discord_handle: '' })

const membership = computed(() => myMemberships.value[0] || null)
const canApply = computed(() => isAuthenticated.value && (!membership.value || membership.value.status === 'inactive'))
const hasMembership = computed(() => Boolean(membership.value && ['active', 'pending'].includes(membership.value.status)))

function openApplication() {
  applicationError.value = ''
  applicationSuccess.value = ''
  applicationOpen.value = true
  applicationNote.value = membership.value?.note || ''
  applicationDetails.value = {
    availability: membership.value?.availability || '',
    preferred_ships: membership.value?.preferred_ships || '',
    timezone: membership.value?.timezone || '',
    discord_handle: membership.value?.discord_handle || '',
  }
}

function closeApplication() {
  applicationOpen.value = false
  applicationNote.value = ''
  applicationDetails.value = { availability: '', preferred_ships: '', timezone: '', discord_handle: '' }
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

async function loadFleet() {
  loading.value = true
  error.value = ''
  try {
    fleet.value = await getOfficialFleet()
    await loadMemberships()
  } catch (err) {
    error.value = err.message || t('fleets.loadError')
  } finally {
    loading.value = false
  }
}

async function submitApplication() {
  applying.value = true
  applicationError.value = ''
  applicationSuccess.value = ''
  try {
    await joinFleet({
      fleet_id: fleet.value?.id || null,
      note: applicationNote.value || null,
      availability: applicationDetails.value.availability || null,
      preferred_ships: applicationDetails.value.preferred_ships || null,
      timezone: applicationDetails.value.timezone || null,
      discord_handle: applicationDetails.value.discord_handle || null,
    })
    applicationSuccess.value = t('fleets.application.sent', { fleet: fleet.value?.name || t('common.fleets') })
    closeApplication()
    await loadFleet()
  } catch (err) {
    applicationError.value = err.message || t('fleets.application.error')
  } finally {
    applying.value = false
  }
}

onMounted(loadFleet)
</script>

<template>
  <section class="fleet-page" aria-labelledby="fleet-title">
    <div class="wire-frame page-frame fleet-frame single-fleet-frame">
      <header class="wire-section page-hero fleet-hero single-fleet-hero">
        <div>
          <p class="eyebrow">{{ t('fleets.eyebrow') }}</p>
          <h1 id="fleet-title">{{ t('fleets.title') }}</h1>
          <p>{{ t('fleets.subtitle') }}</p>
        </div>
        <div class="hero-action-stack">
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/fleets">{{ t('fleets.manageCta') }}</RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/register?fleet=apply">{{ t('fleets.application.applyWithoutLogin') }}</RouterLink>
          <RouterLink v-if="isAuthenticated && hasMembership" class="button-box" to="/profile">{{ t('fleets.profileCta') }}</RouterLink>
        </div>
      </header>

      <p v-if="loading" class="muted table-state">{{ t('fleets.loading') }}</p>
      <p v-else-if="error" class="error-text table-state">{{ error }}</p>
      <p v-if="applicationError" class="error-text table-state">{{ applicationError }}</p>
      <p v-if="applicationSuccess" class="success-text table-state">{{ applicationSuccess }}</p>

      <section v-if="!loading && !error && fleet" class="single-fleet-layout">
        <article class="wire-section fleet-card single-fleet-card">
          <div class="fleet-card-header">
            <span class="summary-pill">{{ t('fleets.singleBadge') }}</span>
            <span class="muted">{{ t('fleets.memberSummary', { active: fleet.active_members_count, pending: fleet.pending_members_count }) }}</span>
          </div>
          <h2>{{ fleet.name }}</h2>
          <p>{{ fleet.description || t('fleets.noDescription') }}</p>
          <div v-if="fleet.standing_orders" class="fleet-orders-block">
            <strong>{{ t('fleets.standingOrders') }}</strong>
            <p>{{ fleet.standing_orders }}</p>
          </div>
          <div class="fleet-leaders">
            <strong>{{ t('fleets.leadership') }}</strong>
            <span v-if="fleet.leaders.length === 0" class="muted">{{ t('fleets.noLeaders') }}</span>
            <span v-for="leader in fleet.leaders" :key="leader.id" class="summary-pill">{{ leader.user.display_name }} · {{ t(`fleets.roles.${leader.role}`) }}</span>
          </div>
        </article>

        <aside class="wire-section fleet-join-panel">
          <p class="eyebrow">{{ t('fleets.application.myStatus') }}</p>
          <h2>{{ t('fleets.application.title') }}</h2>
          <p>{{ t('fleets.application.subtitle') }}</p>

          <div v-if="membership" class="fleet-status-stack">
            <span class="summary-pill fleet-status-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
            <span class="summary-pill">{{ t(`fleets.roles.${membership.role}`) }}</span>
            <small v-if="membership.availability">{{ t('fleets.directory.availability') }}: {{ membership.availability }}</small>
          </div>
          <p v-else class="muted">{{ t('fleets.application.empty') }}</p>

          <template v-if="isAuthenticated">
            <button v-if="canApply" class="form-button primary-action" type="button" @click="openApplication">
              {{ membership?.status === 'inactive' ? t('fleets.application.reapply') : t('fleets.application.apply') }}
            </button>
          </template>
          <RouterLink v-else class="button-box" to="/register?fleet=apply">{{ t('fleets.application.applyWithoutLogin') }}</RouterLink>

          <form v-if="applicationOpen" class="fleet-inline-application" @submit.prevent="submitApplication">
            <label class="input-panel embedded-field">
              <span>{{ t('fleets.application.noteLabel') }}</span>
              <textarea v-model="applicationNote" rows="4" maxlength="1000" :placeholder="t('fleets.application.notePlaceholder')" />
            </label>
            <div class="directory-form-grid">
              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.availability') }}</span>
                <input v-model="applicationDetails.availability" maxlength="240" :placeholder="t('fleets.directory.availabilityPlaceholder')" />
              </label>
              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.preferredShips') }}</span>
                <input v-model="applicationDetails.preferred_ships" maxlength="300" :placeholder="t('fleets.directory.preferredShipsPlaceholder')" />
              </label>
              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.timezone') }}</span>
                <input v-model="applicationDetails.timezone" maxlength="80" placeholder="CET / UTC+1" />
              </label>
              <label class="input-panel embedded-field">
                <span>{{ t('fleets.directory.discord') }}</span>
                <input v-model="applicationDetails.discord_handle" maxlength="120" placeholder="Captain#1234" />
              </label>
            </div>
            <div class="form-actions compact-actions">
              <button class="form-button primary-action" type="submit" :disabled="applying">
                {{ applying ? t('common.saving') : t('fleets.application.submit') }}
              </button>
              <button class="form-button secondary-action" type="button" @click="closeApplication">{{ t('common.cancel') }}</button>
            </div>
          </form>
        </aside>
      </section>
    </div>
  </section>
</template>
