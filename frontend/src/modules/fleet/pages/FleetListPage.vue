<script setup>
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getOfficialFleet, joinFleet, listMyFleetMemberships } from '@/modules/fleet/api/fleet'

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
const leaderCount = computed(() => fleet.value?.leaders?.length || 0)
const totalMembers = computed(() => (fleet.value?.active_members_count || 0) + (fleet.value?.pending_members_count || 0))

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
    <div class="wire-frame page-frame fleet-frame fleet-portal-frame">
      <PageHeader
        :eyebrow="t('fleets.eyebrow')"
        :title="t('fleets.title')"
        :description="t('fleets.subtitle')"
        title-id="fleet-title"
      >
        <template #meta>
          <span class="summary-pill">{{ t('fleets.singleBadge') }}</span>
          <span v-if="membership" class="summary-pill fleet-status-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/builds">{{ t('common.builds') }}</RouterLink>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" :to="hasMembership ? '/profile' : '/fleets'">
            {{ hasMembership ? t('fleets.profileCta') : t('fleets.manageCta') }}
          </RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/register?fleet=apply">{{ t('fleets.application.applyWithoutLogin') }}</RouterLink>
        </template>
      </PageHeader>

      <p v-if="loading" class="muted table-state">{{ t('fleets.loading') }}</p>
      <p v-else-if="error" class="error-text table-state">{{ error }}</p>
      <p v-if="applicationError" class="error-text table-state">{{ applicationError }}</p>
      <p v-if="applicationSuccess" class="success-text table-state">{{ applicationSuccess }}</p>

      <template v-if="!loading && !error && fleet">
        <section class="workspace-metric-grid fleet-portal-metrics" :aria-label="t('fleets.title')">
          <MetricCard :label="t('fleets.manage.summary.active')" :value="fleet.active_members_count" :hint="t('fleets.memberSummary', { active: fleet.active_members_count, pending: fleet.pending_members_count })" tone="accent" />
          <MetricCard :label="t('fleets.manage.summary.pending')" :value="fleet.pending_members_count" />
          <MetricCard :label="t('fleets.leadership')" :value="leaderCount" />
          <MetricCard :label="t('fleets.manage.summary.directory')" :value="totalMembers" />
        </section>

        <div class="fleet-portal-layout">
          <main class="fleet-portal-main">
            <article class="wire-section fleet-briefing-panel">
              <div class="workspace-section-heading">
                <div>
                  <p class="eyebrow">{{ t('fleets.filterEyebrow') }}</p>
                  <h2>{{ fleet.name }}</h2>
                  <p>{{ fleet.description || t('fleets.noDescription') }}</p>
                </div>
                <span class="summary-pill">{{ t(`fleets.focus.${fleet.focus}`) }}</span>
              </div>

              <section class="fleet-orders-block fleet-orders-briefing">
                <span class="fleet-section-index">01</span>
                <div>
                  <strong>{{ t('fleets.standingOrders') }}</strong>
                  <p>{{ fleet.standing_orders || t('fleets.noDescription') }}</p>
                </div>
              </section>

              <section class="fleet-leadership-block">
                <div class="workspace-section-heading compact-heading">
                  <div><span class="fleet-section-index">02</span><h3>{{ t('fleets.leadership') }}</h3></div>
                </div>
                <p v-if="fleet.leaders.length === 0" class="muted">{{ t('fleets.noLeaders') }}</p>
                <div v-else class="fleet-leadership-grid">
                  <article v-for="leader in fleet.leaders" :key="leader.id" class="fleet-leader-card">
                    <span class="profile-avatar" aria-hidden="true">{{ leader.user.display_name.slice(0, 2).toUpperCase() }}</span>
                    <div><strong>{{ leader.user.display_name }}</strong><small>{{ t(`fleets.roles.${leader.role}`) }}</small></div>
                  </article>
                </div>
              </section>
            </article>

            <section class="wire-section fleet-public-modules">
              <div class="workspace-section-heading">
                <div><p class="eyebrow">{{ t('common.workspace') }}</p><h2>{{ t('common.modules') }}</h2></div>
              </div>
              <div class="fleet-module-grid">
                <RouterLink class="fleet-module-card is-public" to="/builds">
                  <span class="fleet-module-icon"><AppIcon name="builds" :size="20" /></span>
                  <strong>{{ t('common.builds') }}</strong>
                  <small>{{ t('home.showcase.builds.description') }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
                <RouterLink v-if="isAuthenticated" class="fleet-module-card" to="/calendar">
                  <span class="fleet-module-icon"><AppIcon name="calendar" :size="20" /></span>
                  <strong>{{ t('common.calendar') }}</strong>
                  <small>{{ t('calendar.list.subtitle') }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
                <RouterLink v-if="isAuthenticated" class="fleet-module-card" to="/groups">
                  <span class="fleet-module-icon"><AppIcon name="groups" :size="20" /></span>
                  <strong>{{ t('common.groups') }}</strong>
                  <small>{{ t('groups.list.subtitle') }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
                <RouterLink v-if="isAuthenticated" class="fleet-module-card" to="/forum">
                  <span class="fleet-module-icon"><AppIcon name="forum" :size="20" /></span>
                  <strong>{{ t('common.forum') }}</strong>
                  <small>{{ t('forum.list.subtitle') }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
                <RouterLink v-else class="fleet-module-card is-locked" to="/login">
                  <span class="fleet-module-icon"><AppIcon name="lock" :size="20" /></span>
                  <strong>{{ t('auth.loginTitle') }}</strong>
                  <small>{{ t('auth.loginSubtitle') }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
              </div>
            </section>
          </main>

          <aside class="fleet-portal-side">
            <section class="wire-section fleet-join-panel polished-join-panel">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('fleets.application.myStatus') }}</p><h2>{{ t('fleets.application.title') }}</h2><p>{{ t('fleets.application.subtitle') }}</p></div>
              </div>

              <div v-if="membership" class="fleet-membership-summary">
                <span class="profile-avatar" aria-hidden="true">{{ membership.user?.display_name?.slice(0, 2).toUpperCase() || 'RBV' }}</span>
                <div><strong>{{ membership.user?.display_name || t('common.profile') }}</strong><small>{{ t(`fleets.roles.${membership.role}`) }}</small></div>
                <span class="summary-pill fleet-status-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
              </div>
              <p v-else class="muted">{{ t('fleets.application.empty') }}</p>

              <template v-if="isAuthenticated">
                <button v-if="canApply" class="form-button primary-action" type="button" @click="openApplication">
                  {{ membership?.status === 'inactive' ? t('fleets.application.reapply') : t('fleets.application.apply') }}
                </button>
                <RouterLink v-else class="button-box" to="/profile">{{ t('fleets.profileCta') }}</RouterLink>
              </template>
              <template v-else>
                <RouterLink class="button-box primary-action" to="/register?fleet=apply">{{ t('fleets.application.applyWithoutLogin') }}</RouterLink>
                <RouterLink class="button-box" to="/login">{{ t('auth.login') }}</RouterLink>
              </template>

              <form v-if="applicationOpen" class="fleet-inline-application" @submit.prevent="submitApplication">
                <label class="input-panel embedded-field">
                  <span>{{ t('fleets.application.noteLabel') }}</span>
                  <textarea v-model="applicationNote" rows="4" maxlength="1000" :placeholder="t('fleets.application.notePlaceholder')" />
                </label>
                <div class="directory-form-grid">
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.availability') }}</span><input v-model="applicationDetails.availability" maxlength="240" :placeholder="t('fleets.directory.availabilityPlaceholder')" /></label>
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.preferredShips') }}</span><input v-model="applicationDetails.preferred_ships" maxlength="300" :placeholder="t('fleets.directory.preferredShipsPlaceholder')" /></label>
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.timezone') }}</span><input v-model="applicationDetails.timezone" maxlength="80" placeholder="CET / UTC+1" /></label>
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.discord') }}</span><input v-model="applicationDetails.discord_handle" maxlength="120" placeholder="Captain#1234" /></label>
                </div>
                <div class="form-actions compact-actions">
                  <button class="form-button primary-action" type="submit" :disabled="applying">{{ applying ? t('common.saving') : t('fleets.application.submit') }}</button>
                  <button class="form-button secondary-action" type="button" @click="closeApplication">{{ t('common.cancel') }}</button>
                </div>
              </form>
            </section>

            <section class="wire-section fleet-access-panel">
              <p class="eyebrow">{{ t('auth.registerBenefitsLabel') }}</p>
              <div class="fleet-access-list">
                <span><b>01</b>{{ t('auth.registerBenefit.profile') }}</span>
                <span><b>02</b>{{ t('auth.registerBenefit.fleet') }}</span>
                <span><b>03</b>{{ t('auth.registerBenefit.tools') }}</span>
              </div>
            </section>
          </aside>
        </div>
      </template>
    </div>
  </section>
</template>
