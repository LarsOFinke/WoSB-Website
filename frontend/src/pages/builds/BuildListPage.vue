<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listBuilds } from '@/services/builds'

const { optionLabel, t } = useLocale()

const builds = ref([])
const search = ref('')
const buildType = ref('')
const loading = ref(false)
const error = ref('')
let searchTimer = null

const buildTypeOptions = computed(() => [
  { value: '', label: t('builds.types.all') },
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])

const buildTypeLabels = computed(() => Object.fromEntries(buildTypeOptions.value.map((option) => [option.value, option.label])))

const buildCountLabel = computed(() => {
  if (builds.value.length === 1) {
    return t('builds.list.summaryOne')
  }
  return t('builds.list.summaryMany', { count: builds.value.length })
})

function buildTypeLabel(value) {
  return buildTypeLabels.value[value] || value || t('builds.types.balanced')
}

function crewTotal(build) {
  return build.sailors + build.soldiers + build.musketeers + build.mercenaries
}

function slotSummary(build) {
  const slots = [build.upgrade_1, build.upgrade_2, build.upgrade_3, build.upgrade_4, build.upgrade_5]
    .filter(Boolean)
    .length
  return t('builds.list.upgradeSummary', { used: slots })
}

function inventorySummary(build) {
  const ammoCount = build.ammunition_slots?.length || 0
  const consumableCount = build.consumable_slots?.length || 0
  const holdCount = build.hold_slots?.length || 0
  return t('builds.list.inventorySummary', {
    ammo: ammoCount,
    consumables: consumableCount,
    hold: holdCount,
  })
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

async function loadBuilds() {
  loading.value = true
  error.value = ''
  try {
    builds.value = await listBuilds(search.value, buildType.value)
  } catch (err) {
    error.value = err.message || t('builds.list.loadError')
  } finally {
    loading.value = false
  }
}

watch([search, buildType], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

onMounted(loadBuilds)
</script>

<template>
  <section class="build-list-page" aria-labelledby="builds-title">
    <div class="wire-frame page-frame compact-frame build-list-frame">
      <header class="wire-section build-list-hero">
        <div>
          <p class="eyebrow">{{ t('common.builds') }}</p>
          <h1 id="builds-title">{{ t('builds.list.title') }}</h1>
          <p>{{ t('builds.list.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ buildCountLabel }}</span>
          <RouterLink class="button-box primary-action" to="/builds/new">
            {{ t('builds.list.newBuild') }}
          </RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel" :aria-label="t('builds.list.info', { summary: buildCountLabel })">
        <div>
          <h2>{{ t('builds.list.info', { summary: buildCountLabel }) }}</h2>
          <p>{{ t('builds.list.subtitle') }}</p>
        </div>
        <div class="list-toolbar has-type-filter refined-toolbar">
          <label class="filter-box search-filter-box">
            <input v-model="search" type="search" :placeholder="t('builds.list.searchPlaceholder')" />
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

      <section class="wire-section filter-table build-results-panel">
        <p v-if="loading" class="muted table-state">{{ t('builds.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="builds.length === 0" class="muted table-state">{{ t('builds.list.empty') }}</p>

        <div v-else class="build-card-list refined-card-list">
          <RouterLink
            v-for="build in builds"
            :key="build.id"
            class="build-list-card refined-build-card"
            :to="`/builds/${build.id}`"
          >
            <div class="build-card-main">
              <div>
                <strong>{{ build.build_name }}</strong>
                <span>{{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ build.ship.ship_type }}</span>
              </div>
              <span class="type-pill">{{ buildTypeLabel(build.build_type) }}</span>
            </div>

            <div class="build-card-meta refined-meta">
              <span>{{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}</span>
              <span>{{ t('builds.list.sailorMin', { value: build.ship.sailor_minimum }) }}</span>
              <span>{{ slotSummary(build) }}</span>
              <span>{{ inventorySummary(build) }}</span>
            </div>

            <div class="build-card-preview refined-preview">
              <span>{{ t('builds.list.ammunitionPreview', { items: previewItems(build.ammunition_slots) }) }}</span>
              <span>{{ t('builds.list.consumablesPreview', { items: previewItems(build.consumable_slots) }) }}</span>
              <span>{{ t('builds.list.holdPreview', { items: previewItems(build.hold_slots) }) }}</span>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
