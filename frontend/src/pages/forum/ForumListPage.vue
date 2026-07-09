<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listThreads } from '@/services/forum'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()

const threads = ref([])
const search = ref('')
const category = ref('')
const loading = ref(false)
const error = ref('')
let searchTimer = null

const categories = computed(() => [
  { value: '', label: t('forum.categories.all') },
  { value: 'general', label: t('forum.categories.general') },
  { value: 'builds', label: t('forum.categories.builds') },
  { value: 'events', label: t('forum.categories.events') },
  { value: 'support', label: t('forum.categories.support') },
  { value: 'training', label: t('forum.categories.training') },
  { value: 'logistics', label: t('forum.categories.logistics') },
])

const summary = computed(() => threads.value.length === 1 ? t('forum.list.summaryOne') : t('forum.list.summaryMany', { count: threads.value.length }))

function normalizeForumCategory(value) {
  const normalized = String(value || 'general').trim().toLowerCase()
  if (normalized === 'loistics' || normalized === 'logistic') return 'logistics'
  return normalized || 'general'
}

function categoryLabel(value) {
  return t(`forum.categories.${normalizeForumCategory(value)}`)
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

async function loadThreads() {
  loading.value = true
  error.value = ''
  try {
    threads.value = await listThreads(search.value, category.value)
  } catch (err) {
    error.value = err.message || t('forum.list.loadError')
  } finally {
    loading.value = false
  }
}

watch([search, category], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadThreads, 220)
})

onMounted(loadThreads)
</script>

<template>
  <section class="forum-page" aria-labelledby="forum-title">
    <div class="wire-frame page-frame compact-frame forum-frame">
      <header class="wire-section build-list-hero forum-hero">
        <div>
          <p class="eyebrow">{{ t('common.forum') }}</p>
          <h1 id="forum-title">{{ t('forum.list.title') }}</h1>
          <p>{{ t('forum.list.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ summary }}</span>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/forum/new">
            {{ t('forum.list.newThread') }}
          </RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/login">
            {{ t('forum.list.loginToCreate') }}
          </RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel">
        <div>
          <h2>{{ t('forum.list.filtersTitle') }}</h2>
          <p>{{ t('forum.list.filtersText') }}</p>
        </div>
        <div class="list-toolbar has-type-filter refined-toolbar">
          <label class="filter-box search-filter-box">
            <input v-model="search" type="search" :placeholder="t('forum.list.searchPlaceholder')" />
          </label>
          <label class="filter-box type-filter-box select-shell toolbar-select-shell">
            <select v-model="category">
              <option v-for="option in categories" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
        </div>
      </section>

      <section class="wire-section filter-table forum-results-panel">
        <p v-if="loading" class="muted table-state">{{ t('forum.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="threads.length === 0" class="muted table-state">{{ t('forum.list.empty') }}</p>

        <div v-else class="build-card-list refined-card-list forum-card-list">
          <RouterLink v-for="thread in threads" :key="thread.id" class="build-list-card refined-build-card forum-list-card" :to="`/forum/${thread.id}`">
            <div class="build-card-main">
              <div>
                <strong>{{ thread.title }}</strong>
                <span>{{ categoryLabel(thread.category) }} · {{ t('forum.list.by', { name: thread.owner.display_name }) }}</span>
              </div>
              <span class="type-pill">{{ t('forum.list.replies', { count: thread.reply_count }) }}</span>
            </div>
            <div class="build-card-meta refined-meta">
              <span>{{ t('forum.list.lastActivity', { value: formatDate(thread.last_activity_at) }) }}</span>
              <span>{{ t('forum.list.created', { value: formatDate(thread.created_at) }) }}</span>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
