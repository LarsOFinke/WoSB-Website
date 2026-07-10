<script setup>
import { computed } from 'vue'

import fleetIconUrl from '@/assets/rbf-fleet-icon.png'
import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()

const newcomerSteps = computed(() => [
  { number: '01', icon: 'compass', title: t('home.newcomer.guideTitle'), text: t('home.newcomer.guideText'), meta: t('home.newcomer.guideMeta'), path: '/new-captain' },
  { number: '02', icon: 'guides', title: t('home.newcomer.learnTitle'), text: t('home.newcomer.learnText'), meta: t('home.newcomer.learnMeta'), path: '/guides' },
  { number: '03', icon: 'builds', title: t('home.newcomer.prepareTitle'), text: t('home.newcomer.prepareText'), meta: t('home.newcomer.prepareMeta'), path: '/builds' },
  { number: '04', icon: 'forum', title: t('home.newcomer.askTitle'), text: t('home.newcomer.askText'), meta: t('home.newcomer.askMeta'), path: '/forum' },
  { number: '05', icon: 'calendar', title: t('home.newcomer.joinTitle'), text: t('home.newcomer.joinText'), meta: t('home.newcomer.joinMeta'), path: '/calendar' },
])

const memberModules = computed(() => [
  { icon: 'compass', title: t('common.newCaptainGuide'), text: t('home.newcomer.guideText'), path: '/new-captain' },
  { icon: 'builds', title: t('home.showcase.builds.title'), text: t('home.showcase.builds.description'), path: '/builds' },
  { icon: 'guides', title: t('home.showcase.guides.title'), text: t('home.showcase.guides.description'), path: '/guides' },
  { icon: 'forum', title: t('home.showcase.forum.title'), text: t('home.showcase.forum.description'), path: '/forum' },
  { icon: 'calendar', title: t('home.showcase.calendar.title'), text: t('home.showcase.calendar.description'), path: '/calendar' },
])

function memberRoute(path) {
  if (isAuthenticated.value) return path
  return { name: 'login', query: { redirect: path } }
}
</script>

<template>
  <section class="fleet-page" aria-labelledby="landing-title">
    <div class="wire-frame page-frame fleet-frame fleet-portal-frame public-landing-frame">
      <PageHeader
        :eyebrow="t('home.eyebrow')"
        :title="t('home.title')"
        :description="t('home.subtitle')"
        title-id="landing-title"
      >
        <template #meta>
          <span class="summary-pill">{{ t('home.publicAccessBadge') }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/fleet">{{ t('common.fleetOverview') }}</RouterLink>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/new-captain">{{ t('common.newCaptainGuide') }}</RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/register">{{ t('home.joinCta') }}</RouterLink>
        </template>
      </PageHeader>

      <div class="fleet-portal-layout public-landing-layout">
        <main class="fleet-portal-main">
          <article class="wire-section fleet-briefing-panel fleet-identity-panel">
            <div class="workspace-section-heading fleet-identity-heading">
              <div>
                <p class="eyebrow">{{ t('home.aboutEyebrow') }}</p>
                <h2>{{ t('home.aboutTitle') }}</h2>
                <p>{{ t('home.about') }}</p>
                <p class="fleet-identity-extra">{{ t('home.aboutExtra') }}</p>
              </div>
              <figure class="fleet-crest-card public-fleet-crest">
                <img :src="fleetIconUrl" :alt="t('common.projectName')" loading="eager" decoding="async" />
              </figure>
            </div>
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
                :class="{ 'is-locked': !isAuthenticated }"
                :to="memberRoute(step.path)"
              >
                <span class="newcomer-step-number">{{ step.number }}</span>
                <span class="fleet-module-icon"><AppIcon :name="step.icon" :size="20" /></span>
                <strong>{{ step.title }}</strong>
                <p>{{ step.text }}</p>
                <small>{{ step.meta }}</small>
                <AppIcon v-if="!isAuthenticated" class="newcomer-step-arrow" name="lock" :size="15" />
                <AppIcon v-else class="newcomer-step-arrow" name="arrow-right" :size="17" />
              </RouterLink>
            </div>
          </section>

          <section class="wire-section fleet-public-modules">
            <div class="workspace-section-heading">
              <div>
                <p class="eyebrow">{{ t('home.showcase.eyebrow') }}</p>
                <h2>{{ t('home.showcase.title') }}</h2>
                <p>{{ t('home.memberGateText') }}</p>
              </div>
            </div>
            <div class="fleet-module-grid fleet-learning-module-grid">
              <RouterLink
                v-for="module in memberModules"
                :key="module.path"
                class="fleet-module-card is-locked"
                :to="memberRoute(module.path)"
              >
                <span class="fleet-module-icon"><AppIcon :name="module.icon" :size="20" /></span>
                <span class="fleet-module-access">
                  <AppIcon v-if="!isAuthenticated" name="lock" :size="13" />
                  {{ isAuthenticated ? t('home.showcase.memberModule') : t('home.loginRequired') }}
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
          </section>

          <section class="wire-section fleet-access-panel public-access-panel">
            <p class="eyebrow">{{ t('home.publicAreaTitle') }}</p>
            <h2>{{ t('home.publicAreaHeading') }}</h2>
            <p>{{ t('home.publicAreaText') }}</p>
            <RouterLink class="button-box" to="/fleet">{{ t('common.fleetOverview') }}</RouterLink>
            <RouterLink v-if="!isAuthenticated" class="button-box primary-action" to="/login">{{ t('auth.login') }}</RouterLink>
          </section>
        </aside>
      </div>
    </div>
  </section>
</template>
