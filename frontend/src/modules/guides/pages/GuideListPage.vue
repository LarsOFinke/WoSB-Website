<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import GuideResultList from '@/modules/guides/components/GuideResultList.vue'
import GuideTopicRail from '@/modules/guides/components/GuideTopicRail.vue'
import { listGuides } from '@/modules/guides/api/guides'
import { localizedGuideDiscoveryGroups } from '@/modules/guides/domain/guideDiscovery'
import '@/modules/guides/styles/guides.css'

const { t } = useLocale()
const { isAuthenticated } = useSession()
const guides = ref([])
const search = ref('')
const category = ref('')
const showAll = ref(false)
const loading = ref(false)
const error = ref('')
let searchTimer = null

const discoveryGroups = computed(() => localizedGuideDiscoveryGroups(t))
const hasActiveDiscovery = computed(() => showAll.value || Boolean(search.value.trim() || category.value))
const summary = computed(() => guides.value.length === 1
  ? t('guides.list.summaryOne')
  : t('guides.list.summaryMany', { count: guides.value.length }))
const selectedCategoryLabel = computed(() => discoveryGroups.value
  .flatMap((group) => group.items)
  .find((item) => item.value === category.value)?.label || t('discovery.guides.allResults'))

async function loadGuides() {
  if (!hasActiveDiscovery.value) {
    guides.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    guides.value = await listGuides(search.value, category.value)
  } catch (err) {
    error.value = err.message || t('guides.list.loadError')
  } finally {
    loading.value = false
  }
}

function resetDiscovery() {
  search.value = ''
  category.value = ''
  showAll.value = false
  guides.value = []
  error.value = ''
}

function showAllGuides() {
  showAll.value = true
  category.value = ''
  loadGuides()
}

watch([search, category], () => {
  showAll.value = false
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadGuides, 220)
})

onBeforeUnmount(() => window.clearTimeout(searchTimer))
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
