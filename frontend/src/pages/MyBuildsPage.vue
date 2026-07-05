<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { deleteMyBuild, listMyBuilds } from '@/services/builds'

const { optionLabel, t } = useLocale()

const builds = ref([])
const search = ref('')
const buildType = ref('')
const loading = ref(false)
const error = ref('')
const pendingDeleteId = ref(null)
let searchTimer = null

const buildTypeOptions = computed(() => [
  { value: '', label: t('builds.types.all') },
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])

const buildCountLabel = computed(() =>
  builds.value.length === 1 ? t('myBuilds.summaryOne') : t('myBuilds.summaryMany', { count: builds.value.length }),
)

function crewTotal(build) {
  return build.sailors + build.soldiers + build.musketeers + build.mercenaries
}

function slotLabel(slot) {
  if (typeof slot === 'string') return optionLabel(slot)
  if (!slot?.item) return ''
  return `${optionLabel(slot.item)} ×${slot.quantity || 1}`
}

function previewItems(items) {
  const labels = (items || []).map(slotLabel).filter(Boolean)
  if (!labels.length) return t('builds.list.noSlots')
  return labels.slice(0, 2).join(', ') + (labels.length > 2 ? ' …' : '')
}

async function loadMyBuilds() {
  loading.value = true
  error.value = ''
  try {
    builds.value = await listMyBuilds(search.value, buildType.value)
  } catch (err) {
    error.value = err.message || t('myBuilds.loadError')
  } finally {
    loading.value = false
  }
}

async function confirmDelete(buildId) {
  error.value = ''
  try {
    await deleteMyBuild(buildId)
    pendingDeleteId.value = null
    await loadMyBuilds()
  } catch (err) {
    error.value = err.message || t('myBuilds.deleteError')
  }
}

watch([search, buildType], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadMyBuilds, 220)
})

onMounted(loadMyBuilds)
</script>

<template>
  <section class="my-builds-page" aria-labelledby="my-builds-title">
    <div class="wire-frame page-frame compact-frame my-builds-frame">
      <header class="wire-section build-list-hero my-builds-hero">
        <div>
          <p class="eyebrow">{{ t('myBuilds.eyebrow') }}</p>
          <h1 id="my-builds-title">{{ t('myBuilds.title') }}</h1>
          <p>{{ t('myBuilds.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ buildCountLabel }}</span>
          <RouterLink class="button-box primary-action" to="/builds/new">{{ t('myBuilds.create') }}</RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel" :aria-label="t('myBuilds.filtersLabel')">
        <div>
          <h2>{{ t('myBuilds.manageTitle') }}</h2>
          <p>{{ t('myBuilds.manageText') }}</p>
        </div>
        <div class="list-toolbar has-type-filter refined-toolbar">
          <label class="filter-box search-filter-box">
            <input v-model="search" type="search" :placeholder="t('myBuilds.searchPlaceholder')" />
          </label>

          <label class="filter-box type-filter-box">
            <select v-model="buildType">
              <option v-for="option in buildTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
      </section>

      <section class="wire-section filter-table build-results-panel user-build-management-panel">
        <p v-if="loading" class="muted table-state">{{ t('myBuilds.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <div v-else-if="builds.length === 0" class="empty-state-block">
          <h2>{{ t('myBuilds.emptyTitle') }}</h2>
          <p>{{ t('myBuilds.emptyText') }}</p>
          <RouterLink class="button-box primary-action" to="/builds/new">{{ t('myBuilds.createFirst') }}</RouterLink>
        </div>

        <div v-else class="my-build-list">
          <article v-for="build in builds" :key="build.id" class="my-build-row">
            <RouterLink class="my-build-row-main" :to="`/builds/${build.id}`">
              <strong>{{ build.build_name }}</strong>
              <span>
                {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} ·
                {{ t(`builds.types.${build.build_type}`) }} ·
                {{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}
              </span>
              <small>
                {{ t('builds.list.ammunitionPreview', { items: previewItems(build.ammunition_slots) }) }} ·
                {{ t('builds.list.holdPreview', { items: previewItems(build.hold_slots) }) }}
              </small>
            </RouterLink>

            <div v-if="pendingDeleteId === build.id" class="delete-confirmation my-build-delete-confirmation">
              <span>{{ t('myBuilds.confirmDelete') }}</span>
              <button class="danger-action" type="button" @click="confirmDelete(build.id)">
                {{ t('myBuilds.deleteNow') }}
              </button>
              <button class="small-action" type="button" @click="pendingDeleteId = null">
                {{ t('common.cancel') }}
              </button>
            </div>

            <button v-else class="danger-action" type="button" @click="pendingDeleteId = build.id">
              {{ t('myBuilds.delete') }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
