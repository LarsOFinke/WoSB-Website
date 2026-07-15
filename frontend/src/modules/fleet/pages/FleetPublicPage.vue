<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import fleetIconUrl from '@/assets/rbf-fleet-icon.png'
import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getPublicOfficialFleet, joinFleet, listMyFleetMemberships } from '@/modules/fleet/api/fleet'

const { t } = useLocale()
const { isAuthenticated } = useSession()
const fleet = ref(null)
const loading = ref(false)
const error = ref('')
const membership = ref(null)
const applying = ref(false)
const applicationError = ref('')
const applicationSuccess = ref('')
const application = reactive({
  note: '',
})

const leaderCount = computed(() => fleet.value?.leaders?.length || 0)
const canApply = computed(() => isAuthenticated.value && (!membership.value || membership.value.status === 'inactive'))
const hasMembership = computed(() => Boolean(membership.value && ['pending', 'active'].includes(membership.value.status)))

async function loadFleet() {
  loading.value = true
  error.value = ''
  try {
    fleet.value = await getPublicOfficialFleet()
    if (isAuthenticated.value) {
      try {
        const memberships = await listMyFleetMemberships()
        membership.value = memberships.find((row) => row.fleet?.id === fleet.value.id) || memberships[0] || null
      } catch (membershipError) {
        applicationError.value = membershipError.message || t('fleets.application.statusError')
      }
    }
  } catch (err) {
    error.value = err.message || t('fleets.loadError')
  } finally {
    loading.value = false
  }
}

async function submitFleetApplication() {
  if (!fleet.value || !canApply.value) return
  applying.value = true
  applicationError.value = ''
  applicationSuccess.value = ''
  try {
    membership.value = await joinFleet({
      fleet_id: fleet.value.id,
      note: application.note.trim() || null,
    })
    applicationSuccess.value = t('fleets.application.submitted')
  } catch (err) {
    applicationError.value = err.message || t('fleets.application.submitError')
  } finally {
    applying.value = false
  }
}

onMounted(loadFleet)
</script>

<template>
  <section class="fleet-page" aria-labelledby="public-fleet-title">
    <div class="wire-frame page-frame fleet-frame fleet-public-frame">
      <PageHeader
        :eyebrow="t('publicFleet.eyebrow')"
        :title="fleet?.name || t('fleets.title')"
        :description="t('publicFleet.subtitle')"
        title-id="public-fleet-title"
      >
        <template #meta>
          <span class="summary-pill">{{ t('publicFleet.publicBadge') }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/">{{ t('common.home') }}</RouterLink>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/profile">{{ t('common.profile') }}</RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/register">{{ t('fleets.application.createAccountFirst') }}</RouterLink>
        </template>
      </PageHeader>

      <p v-if="loading" class="muted table-state">{{ t('fleets.loading') }}</p>
      <p v-else-if="error" class="error-text table-state">{{ error }}</p>

      <template v-if="!loading && !error && fleet">
        <section class="workspace-metric-grid public-fleet-metrics" :aria-label="t('publicFleet.metricsLabel')">
          <MetricCard :label="t('publicFleet.activeMembers')" :value="fleet.active_members_count" tone="accent" />
          <MetricCard :label="t('fleets.leadership')" :value="leaderCount" />
          <MetricCard :label="t('publicFleet.activityWindow')" :value="t('home.operations.activeHoursValue')" />
        </section>

        <div class="fleet-portal-layout public-fleet-layout">
          <main class="fleet-portal-main">
            <article class="wire-section fleet-briefing-panel fleet-identity-panel">
              <div class="workspace-section-heading fleet-identity-heading">
                <div>
                  <p class="eyebrow">{{ t('publicFleet.aboutEyebrow') }}</p>
                  <h2>{{ t('home.aboutTitle') }}</h2>
                  <p>{{ fleet.description || t('fleets.publicDescription') }}</p>
                  <p class="fleet-identity-extra">{{ t('home.aboutExtra') }}</p>
                </div>
                <div class="fleet-identity-badge-group">
                  <span class="summary-pill">{{ t(`fleets.focus.${fleet.focus}`) }}</span>
                  <figure class="fleet-crest-card">
                    <img :src="fleetIconUrl" :alt="fleet.name" loading="eager" decoding="async" />
                  </figure>
                </div>
              </div>

              <section class="fleet-orders-block fleet-orders-briefing">
                <span class="fleet-section-index">01</span>
                <div>
                  <strong>{{ t('fleets.standingOrders') }}</strong>
                  <p>{{ fleet.standing_orders || t('home.operations.standingOrders') }}</p>
                </div>
              </section>

              <section class="fleet-leadership-block">
                <div class="workspace-section-heading compact-heading">
                  <div><span class="fleet-section-index">02</span><h3>{{ t('fleets.leadership') }}</h3></div>
                </div>
                <p v-if="fleet.leaders.length === 0" class="muted">{{ t('fleets.noLeaders') }}</p>
                <div v-else class="fleet-leadership-grid">
                  <article v-for="leader in fleet.leaders" :key="`${leader.display_name}-${leader.role}`" class="fleet-leader-card">
                    <span class="profile-avatar" aria-hidden="true">{{ leader.display_name.slice(0, 2).toUpperCase() }}</span>
                    <div><strong>{{ leader.display_name }}</strong><small>{{ leader.role_label || t(`fleets.roles.${leader.role}`) }}</small></div>
                  </article>
                </div>
              </section>
            </article>
          </main>

          <aside class="fleet-portal-side">
            <section class="wire-section fleet-operations-panel">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('home.operations.eyebrow') }}</p><h2>{{ t('home.operations.title') }}</h2></div>
              </div>
              <dl class="fleet-rhythm-list">
                <div><dt>{{ t('home.operations.activeHoursLabel') }}</dt><dd>{{ t('home.operations.activeHoursValue') }}</dd></div>
                <div><dt>{{ t('home.operations.primeTimeLabel') }}</dt><dd>{{ t('home.operations.primeTimeValue') }}</dd></div>
                <div><dt>{{ t('home.operations.voiceLabel') }}</dt><dd>{{ t('home.operations.voiceValue') }}</dd></div>
              </dl>
              <div class="fleet-policy-list">
                <p><AppIcon name="calendar" :size="17" /><span>{{ t('home.operations.calendarRule') }}</span></p>
                <p><AppIcon name="shield" :size="17" /><span>{{ t('home.operations.voicePolicy') }}</span></p>
              </div>
            </section>

            <section class="wire-section fleet-join-panel polished-join-panel">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('publicFleet.joinEyebrow') }}</p><h2>{{ t('publicFleet.joinTitle') }}</h2><p>{{ t('publicFleet.joinText') }}</p></div>
              </div>
              <form v-if="canApply" class="fleet-application-form" @submit.prevent="submitFleetApplication">
                <label class="input-panel embedded-field textarea-input-panel">
                  <span>{{ t('auth.fleetApplicationNote') }}</span>
                  <textarea v-model="application.note" rows="4" maxlength="1000" :placeholder="t('auth.fleetApplicationNotePlaceholder')"></textarea>
                </label>
                <p class="muted">{{ t('fleets.application.profileDataHint') }}</p>
                <p v-if="applicationError" class="error-text">{{ applicationError }}</p>
                <p v-if="applicationSuccess" class="success-text">{{ applicationSuccess }}</p>
                <button class="button-box primary-action" type="submit" :disabled="applying">{{ applying ? t('fleets.application.submitting') : t('fleets.application.submit') }}</button>
              </form>
              <div v-else-if="hasMembership" class="fleet-membership-status-card">
                <span class="summary-pill">{{ t(`fleets.status.${membership.status}`) }}</span>
                <p>{{ membership.status === 'pending' ? t('fleets.application.pendingText') : t('fleets.application.activeText') }}</p>
                <RouterLink class="button-box" to="/profile">{{ t('common.profile') }}</RouterLink>
              </div>
              <template v-else>
                <RouterLink class="button-box primary-action" to="/register">{{ t('fleets.application.createAccountFirst') }}</RouterLink>
                <RouterLink class="button-box" to="/login">{{ t('auth.login') }}</RouterLink>
              </template>
            </section>
          </aside>
        </div>
      </template>
    </div>
  </section>
</template>
