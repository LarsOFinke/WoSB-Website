<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'

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
  const stats = build.ship_stats || {}
  const used = stats.upgrade_slots_used ?? [build.upgrade_1, build.upgrade_2, build.upgrade_3, build.upgrade_4, build.upgrade_5, build.upgrade_6, build.upgrade_7].filter(Boolean).length
  const max = stats.upgrade_slots_available || 5
  return t('builds.list.upgradeSummary', { used, max })
}

function inventorySummary(build) {
  const stats = build.ship_stats || {}
  return t('builds.list.inventorySummary', {
    ammo: stats.ammunition_slots_used ?? build.ammunition_slots?.length ?? 0,
    consumables: stats.consumable_slots_used ?? build.consumable_slots?.length ?? 0,
    hold: stats.hold_slots_used ?? build.hold_slots?.length ?? 0,
  })
}

function weaponSummary(build) {
  const stats = build.ship_stats || {}
  return t('builds.list.weaponSummary', { count: stats.weapon_total || 0 })
}

function specialCrewSummary(build) {
  const stats = build.ship_stats || {}
  return t('builds.list.specialCrewSummary', { count: stats.special_crew_total || 0 })
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

function specialistPreview(items) {
  const labels = (items || []).map((slot) => optionLabel(typeof slot === 'string' ? slot : slot?.item)).filter(Boolean)
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
              <span>{{ t('builds.list.crew', { current: crewTotal(build), max: (build.ship_stats?.crew_capacity || build.ship.crew_capacity) }) }}</span>
              <span>{{ t('builds.list.sailorMin', { value: (build.ship_stats?.sailor_minimum || build.ship.sailor_minimum) }) }}</span>
              <span>{{ slotSummary(build) }}</span>
              <span>{{ weaponSummary(build) }}</span>
              <span>{{ specialCrewSummary(build) }}</span>
              <span>{{ inventorySummary(build) }}</span>
            </div>

            <div class="build-card-preview refined-preview">
              <span>{{ t('builds.list.weaponPreview', { items: previewItems([...(build.front_weapon_slots || []), ...(build.port_weapon_slots || []), ...(build.starboard_weapon_slots || []), ...(build.rear_weapon_slots || []), ...(build.mortar_weapon_slots || []), ...(build.special_weapon_slots || [])]) }) }}</span>
              <span>{{ t('builds.list.specialCrewPreview', { items: specialistPreview(build.special_crew_slots) }) }}</span>
              <span>{{ t('builds.list.ammunitionPreview', { items: previewItems(build.ammunition_slots) }) }}</span>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
