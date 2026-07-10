<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listGuides } from '@/modules/guides/api/guides'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()
const guides = ref([])
const search = ref('')
const category = ref('')
const loading = ref(false)
const error = ref('')
let searchTimer = null

const categories = computed(() => [
  { value: '', label: t('guides.categories.all') },
  { value: 'general', label: t('guides.categories.general') },
  { value: 'builds', label: t('guides.categories.builds') },
  { value: 'combat', label: t('guides.categories.combat') },
  { value: 'economy', label: t('guides.categories.economy') },
])

const summary = computed(() => guides.value.length === 1 ? t('guides.list.summaryOne') : t('guides.list.summaryMany', { count: guides.value.length }))

function categoryLabel(value) {
  return t(`guides.categories.${value || 'general'}`)
}

async function loadGuides() {
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

watch([search, category], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadGuides, 220)
})

onMounted(loadGuides)
</script>

<template>
  <section class="guides-page" aria-labelledby="guides-title">
    <div class="wire-frame page-frame compact-frame guides-frame">
      <header class="wire-section build-list-hero guides-hero">
        <div>
          <p class="eyebrow">{{ t('common.guides') }}</p>
          <h1 id="guides-title">{{ t('guides.list.title') }}</h1>
          <p>{{ t('guides.list.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ summary }}</span>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/guides/new">
            {{ t('guides.list.newGuide') }}
          </RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/login">
            {{ t('guides.list.loginToCreate') }}
          </RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel">
        <div>
          <h2>{{ t('guides.list.filtersTitle') }}</h2>
          <p>{{ t('guides.list.filtersText') }}</p>
        </div>
        <div class="list-toolbar has-type-filter refined-toolbar">
          <label class="filter-box search-filter-box">
            <input v-model="search" type="search" :placeholder="t('guides.list.searchPlaceholder')" />
          </label>
          <label class="filter-box type-filter-box select-shell toolbar-select-shell">
            <select v-model="category">
              <option v-for="option in categories" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
        </div>
      </section>

      <section class="wire-section filter-table guides-results-panel">
        <p v-if="loading" class="muted table-state">{{ t('guides.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="guides.length === 0" class="muted table-state">{{ t('guides.list.empty') }}</p>

        <div v-else class="build-card-list refined-card-list guides-card-list">
          <RouterLink v-for="guide in guides" :key="guide.id" class="build-list-card refined-build-card guide-list-card" :to="`/guides/${guide.id}`">
            <div class="build-card-main">
              <div>
                <strong>{{ guide.title }}</strong>
                <span>{{ categoryLabel(guide.category) }} · {{ t('guides.list.by', { name: guide.owner.display_name }) }}</span>
              </div>
              <div class="guide-list-pills">
                <span class="type-pill">{{ t('guides.list.attachments', { count: guide.attachment_count }) }}</span>
                <span v-if="guide.build_reference_count" class="type-pill">{{ t('buildEmbeds.referenceCount', { count: guide.build_reference_count }) }}</span>
              </div>
            </div>
            <p class="group-card-description">{{ guide.summary || t('guides.list.noSummary') }}</p>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
