<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import GuideResultList from '@/modules/guides/components/GuideResultList.vue'
import GuideTopicRail from '@/modules/guides/components/GuideTopicRail.vue'
import '@/modules/guides/styles/guides.css'
import { useGuideListPage } from '@/modules/guides/composables/useGuideListPage'

const {
  t,
  isAuthenticated,
  guides,
  search,
  category,
  showAll,
  loading,
  error,
  searchTimer,
  discoveryGroups,
  hasActiveDiscovery,
  summary,
  selectedCategoryLabel,
  loadGuides,
  resetDiscovery,
  showAllGuides,
  localizedGuideDiscoveryGroups,
} = useGuideListPage()
</script>

<template>
  <section class="guide-library-page" aria-labelledby="guides-title">
    <div class="guide-module-frame guide-library-frame">
      <header class="guide-library-header">
        <div>
          <h1 id="guides-title">{{ t('guides.list.title') }}</h1>
          <p>{{ t('guides.list.subtitle') }}</p>
        </div>
        <RouterLink class="guide-primary-action" :to="isAuthenticated ? '/guides/new' : '/login'">
          <span aria-hidden="true">+</span>
          {{ t(isAuthenticated ? 'guides.list.newGuide' : 'guides.list.loginToCreate') }}
        </RouterLink>
      </header>

      <section class="guide-library-toolbar" :aria-label="t('guides.list.filtersTitle')">
        <label class="guide-search-control">
          <AppIcon name="guides" :size="20" />
          <input
            v-model="search"
            type="search"
            :aria-label="t('guides.list.searchPlaceholder')"
            :placeholder="t('guides.list.searchPlaceholder')"
          />
        </label>
        <button type="button" class="guide-toolbar-action" @click="showAllGuides">
          <AppIcon name="compass" :size="19" />
          {{ t('discovery.guides.showAll') }}
        </button>
        <button
          type="button"
          class="guide-toolbar-action is-quiet"
          :disabled="!hasActiveDiscovery"
          @click="resetDiscovery"
        >
          {{ t('discovery.reset') }}
        </button>
      </section>

      <section class="guide-topic-picker" aria-labelledby="guide-discovery-title">
        <div class="guide-topic-intro">
          <h2 id="guide-discovery-title">{{ t('discovery.guides.title') }}</h2>
          <p>{{ t('discovery.guides.hint') }}</p>
        </div>
        <GuideTopicRail v-model="category" :groups="discoveryGroups" />
      </section>

      <section v-if="hasActiveDiscovery" class="guide-results-panel" aria-live="polite">
        <header class="guide-results-header">
          <div>
            <span>{{ t('discovery.results') }}</span>
            <h2>{{ selectedCategoryLabel }}</h2>
          </div>
          <strong>{{ summary }}</strong>
        </header>
        <p v-if="loading" class="guide-state-message">{{ t('guides.list.loading') }}</p>
        <p v-else-if="error" class="guide-state-message error-text">{{ error }}</p>
        <p v-else-if="guides.length === 0" class="guide-state-message">{{ t('guides.list.empty') }}</p>
        <GuideResultList v-else :guides="guides" />
      </section>
    </div>
  </section>
</template>
