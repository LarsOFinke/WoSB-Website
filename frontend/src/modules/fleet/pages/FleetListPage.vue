<script setup>
import { computed, onMounted, ref } from 'vue'

import fleetIconUrl from '@/assets/rbf-fleet-icon.png'
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

const newcomerSteps = computed(() => [
  { number: '01', icon: 'guides', title: t('home.newcomer.learnTitle'), text: t('home.newcomer.learnText'), meta: t('home.newcomer.learnMeta'), path: '/guides', public: false },
  { number: '02', icon: 'builds', title: t('home.newcomer.prepareTitle'), text: t('home.newcomer.prepareText'), meta: t('home.newcomer.prepareMeta'), path: '/builds', public: true },
  { number: '03', icon: 'forum', title: t('home.newcomer.askTitle'), text: t('home.newcomer.askText'), meta: t('home.newcomer.askMeta'), path: '/forum', public: false },
  { number: '04', icon: 'calendar', title: t('home.newcomer.joinTitle'), text: t('home.newcomer.joinText'), meta: t('home.newcomer.joinMeta'), path: '/calendar', public: false },
])

const moduleCards = computed(() => [
  { icon: 'builds', title: t('home.showcase.builds.title'), text: t('home.showcase.builds.description'), path: '/builds', public: true },
  { icon: 'guides', title: t('home.showcase.guides.title'), text: t('home.showcase.guides.description'), path: '/guides', public: false },
  { icon: 'forum', title: t('home.showcase.forum.title'), text: t('home.showcase.forum.description'), path: '/forum', public: false },
  { icon: 'calendar', title: t('home.showcase.calendar.title'), text: t('home.showcase.calendar.description'), path: '/calendar', public: false },
  { icon: 'groups', title: t('home.showcase.groups.title'), text: t('home.showcase.groups.description'), path: '/groups', public: false },
])

function protectedRoute(path, isPublic = false) {
  if (isPublic || isAuthenticated.value) return path
  return { name: 'login', query: { redirect: path } }
}

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
          <RouterLink class="button-box" to="/builds">{{ t('home.showcase.builds.title') }}</RouterLink>
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
            <article class="wire-section fleet-briefing-panel fleet-identity-panel">
              <div class="workspace-section-heading fleet-identity-heading">
                <div>
                  <p class="eyebrow">{{ t('home.aboutEyebrow') }}</p>
                  <h2>{{ t('home.aboutTitle') }}</h2>
                  <p>{{ t('home.about') }}</p>
                  <p class="fleet-identity-extra">{{ t('home.aboutExtra') }}</p>
                </div>
                <div class="fleet-identity-badge-group">
                  <span class="summary-pill">{{ t(`fleets.focus.${fleet.focus}`) }}</span>
                  <figure class="fleet-crest-card">
                    <img :src="fleetIconUrl" :alt="`${fleet.name} emblem`" loading="eager" decoding="async" />
                  </figure>
                </div>
              </div>

              <section class="fleet-orders-block fleet-orders-briefing">
                <span class="fleet-section-index">01</span>
                <div>
                  <strong>{{ t('fleets.standingOrders') }}</strong>
                  <p>{{ t('home.operations.standingOrders') }}</p>
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

            <section class="wire-section newcomer-path-panel">
              <div class="workspace-section-heading">
                <div>
                  <p class="eyebrow">{{ t('home.newcomer.eyebrow') }}</p>
                  <h2>{{ t('home.newcomer.title') }}</h2>
                  <p>{{ t('home.newcomer.subtitle') }}</p>
                </div>
              </div>
              <div class="newcomer-path-grid">
                <RouterLink
                  v-for="step in newcomerSteps"
                  :key="step.number"
                  class="newcomer-step-card"
                  :class="{ 'is-locked': !step.public && !isAuthenticated }"
                  :to="protectedRoute(step.path, step.public)"
                >
                  <span class="newcomer-step-number">{{ step.number }}</span>
                  <span class="fleet-module-icon"><AppIcon :name="step.icon" :size="20" /></span>
                  <strong>{{ step.title }}</strong>
                  <p>{{ step.text }}</p>
                  <small>{{ step.meta }}</small>
                  <AppIcon class="newcomer-step-arrow" name="arrow-right" :size="17" />
                </RouterLink>
              </div>
            </section>

            <section class="wire-section fleet-public-modules">
              <div class="workspace-section-heading">
                <div>
                  <p class="eyebrow">{{ t('home.showcase.eyebrow') }}</p>
                  <h2>{{ t('home.showcase.title') }}</h2>
                  <p>{{ t('home.showcase.subtitle') }}</p>
                </div>
              </div>
              <div class="fleet-module-grid fleet-learning-module-grid">
                <RouterLink
                  v-for="module in moduleCards"
                  :key="module.path"
                  class="fleet-module-card"
                  :class="{ 'is-public': module.public, 'is-locked': !module.public && !isAuthenticated }"
                  :to="protectedRoute(module.path, module.public)"
                >
                  <span class="fleet-module-icon"><AppIcon :name="module.icon" :size="20" /></span>
                  <span class="fleet-module-access">
                    <AppIcon v-if="!module.public && !isAuthenticated" name="lock" :size="13" />
                    {{ module.public ? t('home.showcase.publicModule') : t('home.showcase.memberModule') }}
                  </span>
                  <strong>{{ module.title }}</strong>
                  <small>{{ module.text }}</small>
                  <b aria-hidden="true"><AppIcon name="arrow-right" :size="17" /></b>
                </RouterLink>
              </div>
            </section>
          </main>

          <aside class="fleet-portal-side">
            <section class="wire-section fleet-operations-panel">
              <div class="workspace-section-heading compact-heading">
                <div>
                  <p class="eyebrow">{{ t('home.operations.eyebrow') }}</p>
                  <h2>{{ t('home.operations.title') }}</h2>
                  <p>{{ t('home.operations.subtitle') }}</p>
                </div>
              </div>
              <dl class="fleet-rhythm-list">
                <div><dt>{{ t('home.operations.activeHoursLabel') }}</dt><dd>{{ t('home.operations.activeHoursValue') }}</dd></div>
                <div><dt>{{ t('home.operations.primeTimeLabel') }}</dt><dd>{{ t('home.operations.primeTimeValue') }}</dd></div>
                <div><dt>{{ t('home.operations.voiceLabel') }}</dt><dd>{{ t('home.operations.voiceValue') }}</dd></div>
              </dl>
              <div class="fleet-policy-list">
                <p><AppIcon name="calendar" :size="17" /><span>{{ t('home.operations.calendarRule') }}</span></p>
                <p><AppIcon name="forum" :size="17" /><span>{{ t('home.operations.discordRule') }}</span></p>
                <p><AppIcon name="shield" :size="17" /><span>{{ t('home.operations.voicePolicy') }}</span></p>
              </div>
            </section>

            <section class="wire-section fleet-join-panel polished-join-panel">
              <div class="workspace-section-heading compact-heading">
                <div><p class="eyebrow">{{ t('fleets.application.myStatus') }}</p><h2>{{ t('fleets.application.title') }}</h2><p>{{ t('fleets.application.subtitle') }}</p></div>
              </div>

              <div v-if="membership" class="fleet-membership-summary">
                <span class="profile-avatar" aria-hidden="true">{{ membership.user?.display_name?.slice(0, 2).toUpperCase() || 'RBF' }}</span>
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
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.timezone') }}</span><input v-model="applicationDetails.timezone" maxlength="80" :placeholder="t('fleets.directory.timezonePlaceholder')" /></label>
                  <label class="input-panel embedded-field"><span>{{ t('fleets.directory.discord') }}</span><input v-model="applicationDetails.discord_handle" maxlength="120" :placeholder="t('fleets.directory.discordPlaceholder')" /></label>
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
