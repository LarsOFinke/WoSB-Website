<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import GuideResultList from '@/modules/guides/components/GuideResultList.vue'
import GuideTopicRail from '@/modules/guides/components/GuideTopicRail.vue'
import '@/modules/guides/styles/guideFoundation.css'
import '@/modules/guides/styles/guideLibraryListing.css'
import '@/modules/guides/styles/guideResponsive.css'
import '@/shared/styles/discovery.css'
import { useGuideListPage } from '@/modules/guides/composables/useGuideListPage'

const {
  t,
  canAuthorContent,
  guides,
  search,
  category,
  loading,
  error,
  discoveryGroups,
  hasFilters,
  hasActiveDiscovery,
  summary,
  selectedCategoryLabel,
  resetDiscovery,
  showAllGuides,
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
        <RouterLink v-if="canAuthorContent" class="guide-primary-action" to="/guides/new">
          <span aria-hidden="true">+</span>
          {{ t('guides.list.newGuide') }}
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
          :disabled="!hasFilters"
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
