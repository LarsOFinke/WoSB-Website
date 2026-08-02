<script setup>
import fleetIconUrl from '@/assets/rbf-fleet-icon.png'
import AppIcon from '@/core/components/AppIcon.vue'
import '@/styles/workspaceRefresh.css'
import '@/modules/fleet/styles/fleetPortalRefresh.css'
import { useLandingPage } from '@/modules/fleet/composables/useLandingPage'

const {
  t,
  isAuthenticated,
  publicFleet,
  newcomerSteps,
  memberModules,
  memberRoute,
} = useLandingPage()
</script>

<template>
  <section class="landing-refresh-page" aria-labelledby="landing-title">
    <div class="wire-frame page-frame workspace-refresh-frame landing-refresh-frame">
      <header class="landing-refresh-hero">
        <figure class="landing-refresh-crest">
          <img :src="fleetIconUrl" :alt="t('common.projectName')" loading="eager" decoding="async" />
        </figure>
        <div class="landing-refresh-copy">
          <h1 id="landing-title">{{ t('home.title') }}</h1>
          <p>{{ t('home.subtitle') }}</p>
          <p class="landing-refresh-about">{{ t('home.about') }} {{ t('home.aboutExtra') }}</p>
          <div class="landing-refresh-actions">
            <RouterLink class="button-box" to="/fleet">{{ t('common.fleetOverview') }}</RouterLink>
            <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/new-captain">{{ t('common.newCaptainGuide') }}</RouterLink>
            <RouterLink v-else class="button-box primary-action" to="/register">{{ t('home.joinCta') }}</RouterLink>
          </div>
        </div>
      </header>

      <section class="landing-refresh-journey" aria-labelledby="landing-journey-title">
        <h2 id="landing-journey-title">{{ t('home.newcomer.title') }}</h2>
        <div class="landing-refresh-steps">
          <RouterLink v-for="step in newcomerSteps" :key="step.number" class="landing-refresh-step" :to="memberRoute(step.path)">
            <span class="landing-refresh-step-number">{{ step.number }}</span>
            <span>
              <strong>{{ step.title }}</strong>
              <small>{{ step.text }}</small>
            </span>
          </RouterLink>
        </div>
      </section>

      <div class="landing-refresh-band">
        <section class="landing-refresh-section" aria-labelledby="landing-leadership-title">
          <h2 id="landing-leadership-title">{{ t('fleets.leadership') }}</h2>
          <div v-if="publicFleet?.leaders?.length" class="landing-refresh-leaders">
            <article v-for="leader in publicFleet.leaders" :key="`${leader.display_name}-${leader.role}`" class="landing-refresh-leader">
              <span><AppIcon name="fleet" :size="19" /></span>
              <div><strong>{{ leader.display_name }}</strong><small>{{ leader.role_label || t(`fleets.roles.${leader.role}`) }}</small></div>
            </article>
          </div>
          <p v-else class="landing-refresh-empty">{{ t('fleets.noLeaders') }}</p>
        </section>

        <section class="landing-refresh-section" aria-labelledby="landing-operations-title">
          <h2 id="landing-operations-title">{{ t('home.operations.title') }}</h2>
          <dl class="landing-refresh-operations">
            <div><dt>{{ t('home.operations.activeHoursLabel') }}</dt><dd>{{ t('home.operations.activeHoursValue') }}</dd></div>
            <div><dt>{{ t('home.operations.primeTimeLabel') }}</dt><dd>{{ t('home.operations.primeTimeValue') }}</dd></div>
            <div><dt>{{ t('home.operations.voiceLabel') }}</dt><dd>{{ t('home.operations.voiceValue') }}</dd></div>
          </dl>
        </section>
      </div>

      <section class="landing-refresh-modules" aria-labelledby="landing-modules-title">
        <h2 id="landing-modules-title">{{ t('home.showcase.title') }}</h2>
        <nav class="landing-refresh-module-list" :aria-label="t('home.showcase.title')">
          <RouterLink v-for="module in memberModules" :key="module.path" class="landing-refresh-module" :to="memberRoute(module.path)">
            <AppIcon :name="module.icon" :size="20" />
            <span><strong>{{ module.title }}</strong><small>{{ module.text }}</small></span>
            <AppIcon :name="isAuthenticated ? 'chevron-right' : 'lock'" :size="16" />
          </RouterLink>
        </nav>
      </section>
    </div>
  </section>
</template>
