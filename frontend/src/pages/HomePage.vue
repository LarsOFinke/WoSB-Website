<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'

const { t } = useLocale()

const showcaseModules = computed(() => [
  {
    key: 'builds',
    route: '/builds',
    eyebrow: t('home.showcase.builds.eyebrow'),
    title: t('home.showcase.builds.title'),
    description: t('home.showcase.builds.description'),
    meta: [
      t('home.showcase.builds.metaShips'),
      t('home.showcase.builds.metaDesigner'),
      t('home.showcase.builds.metaInventory'),
    ],
  },
  {
    key: 'groups',
    route: '/groups',
    eyebrow: t('home.showcase.groups.eyebrow'),
    title: t('home.showcase.groups.title'),
    description: t('home.showcase.groups.description'),
    meta: [
      t('home.showcase.groups.metaPublic'),
      t('home.showcase.groups.metaJoin'),
      t('home.showcase.groups.metaManage'),
    ],
  },
])
</script>

<template>
  <section class="home-page" aria-labelledby="home-title">
    <div class="wire-frame page-frame home-frame polished-home-frame enduser-home-frame">
      <header class="wire-section home-hero polished-home-hero enduser-home-hero">
        <div class="home-hero-copy">
          <p class="eyebrow">{{ t('home.eyebrow') }}</p>
          <h1 id="home-title">{{ t('home.title') }}</h1>
          <p>{{ t('home.subtitle') }}</p>
        </div>
      </header>

      <section class="wire-section hub-intro-card refined-intro-card enduser-intro-card" aria-labelledby="hub-intro-title">
        <div>
          <p class="eyebrow">{{ t('home.aboutEyebrow') }}</p>
          <h2 id="hub-intro-title">{{ t('home.aboutTitle') }}</h2>
        </div>
        <div class="hub-intro-copy">
          <p>{{ t('home.about') }}</p>
          <p>{{ t('home.aboutExtra') }}</p>
        </div>
      </section>

      <section class="wire-section hub-showcase refined-showcase enduser-showcase" aria-labelledby="hub-showcase-title">
        <div class="hub-showcase-header">
          <div>
            <p class="eyebrow">{{ t('home.showcase.eyebrow') }}</p>
            <h2 id="hub-showcase-title">{{ t('home.showcase.title') }}</h2>
          </div>
          <p>{{ t('home.showcase.subtitle') }}</p>
        </div>

        <div class="hub-module-grid refined-module-grid enduser-module-grid">
          <article v-for="module in showcaseModules" :key="module.key" class="hub-module-card primary-module-card enduser-module-card">
            <div class="module-card-topline">
              <span>{{ module.eyebrow }}</span>
              <RouterLink class="small-action module-link" :to="module.route">
                {{ t('home.showcase.openModule') }}
              </RouterLink>
            </div>

            <h3>{{ module.title }}</h3>
            <p>{{ module.description }}</p>

            <div class="module-meta-row">
              <span v-for="item in module.meta" :key="item">{{ item }}</span>
            </div>
          </article>

          <article class="hub-module-card is-placeholder secondary-module-card enduser-module-card">
            <div class="module-card-topline">
              <span>{{ t('home.showcase.nextModuleEyebrow') }}</span>
            </div>
            <h3>{{ t('home.showcase.nextModuleTitle') }}</h3>
            <p>{{ t('home.showcase.nextModuleText') }}</p>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
