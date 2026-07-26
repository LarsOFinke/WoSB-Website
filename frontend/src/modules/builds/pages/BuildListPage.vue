<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import BuildDiscoveryRail from '@/modules/builds/components/BuildDiscoveryRail.vue'
import BuildResultTable from '@/modules/builds/components/BuildResultTable.vue'
import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'
import { localizedBuildDiscoveryGroups } from '@/modules/builds/domain/buildDiscovery'
import '@/styles/workspaceRefresh.css'
import '@/modules/builds/styles/buildLibrary.css'

const { t } = useLocale()
const builds = ref([])
const search = ref('')
const buildType = ref('')
const classification = ref('')
const showAll = ref(false)
const loading = ref(false)
const error = ref('')
let searchTimer = null

const discoveryGroups = computed(() => localizedBuildDiscoveryGroups(t))
const hasActiveDiscovery = computed(() => showAll.value || Boolean(search.value.trim() || buildType.value || classification.value))
const buildTypeOptions = computed(() => [
  { value: '', label: t('builds.types.all') },
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])
const buildTypeLabels = computed(() => Object.fromEntries(buildTypeOptions.value.map((option) => [option.value, option.label])))
const buildCountLabel = computed(() => builds.value.length === 1
  ? t('builds.list.summaryOne')
  : t('builds.list.summaryMany', { count: builds.value.length }))
const selectedDiscoveryLabel = computed(() => {
  const item = discoveryGroups.value.flatMap((group) => group.items).find(({ value }) => value === classification.value)
  return item?.label || t('discovery.builds.allResults')
})
const resultLabels = computed(() => ({
  results: t('discovery.results'),
  build: t('common.builds'),
  type: t('common.type'),
  crew: t('common.crew'),
  upgrades: t('common.upgrades'),
  weapons: t('builds.create.sections.weapons'),
  specialists: t('builds.create.sections.specialCrew'),
  inventory: t('builds.create.sections.inventory'),
}))
const buildRows = computed(() => builds.value.map((build) => {
  const stats = build.ship_stats || {}
  const usedUpgrades = stats.upgrade_slots_used ?? [1, 2, 3, 4, 5, 6, 7, 8].filter((index) => build[`upgrade_${index}`]).length
  const crew = (build.sailors || 0) + (build.soldiers || 0) + (build.musketeers || 0) + (build.mercenaries || 0)
  return {
    id: build.id,
    name: build.build_name,
    ship: [build.ship?.name, build.ship?.rate ? `${t('common.rate')} ${build.ship.rate}` : '', build.ship?.ship_type].filter(Boolean).join(' · '),
    type: buildTypeLabels.value[build.build_type] || build.build_type || t('builds.types.balanced'),
    crew: t('builds.list.crew', { current: crew, max: stats.crew_capacity || build.ship?.crew_capacity || 0 }),
    upgrades: t('builds.list.upgradeSummary', { used: usedUpgrades, max: stats.upgrade_slots_available || 5 }),
    weapons: t('builds.list.weaponSummary', { count: stats.weapon_total || 0 }),
    specialists: t('builds.list.specialCrewSummary', { count: stats.special_crew_total || 0 }),
    inventory: t('builds.list.inventorySummary', {
      ammo: stats.ammunition_slots_used ?? build.ammunition_slots?.length ?? 0,
      consumables: stats.consumable_slots_used ?? build.consumable_slots?.length ?? 0,
      hold: stats.hold_slots_used ?? build.hold_slots?.length ?? 0,
    }),
  }
}))

async function loadBuilds() {
  if (!hasActiveDiscovery.value) {
    builds.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    builds.value = await listBuilds(search.value, buildType.value, classification.value)
  } catch (err) {
    error.value = err.message || t('builds.list.loadError')
  } finally {
    loading.value = false
  }
}

function resetDiscovery() {
  search.value = ''
  buildType.value = ''
  classification.value = ''
  showAll.value = false
  builds.value = []
  error.value = ''
}

function showAllBuilds() {
  showAll.value = true
  classification.value = ''
  loadBuilds()
}

watch([search, buildType, classification], () => {
  showAll.value = false
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

onBeforeUnmount(() => window.clearTimeout(searchTimer))
</script>

<template>
  <section class="build-library-page" aria-labelledby="builds-title">
    <div class="wire-frame page-frame build-library-frame">
      <header class="workspace-command-header">
        <div>
          <h1 id="builds-title">{{ t('builds.list.title') }}</h1>
          <p>{{ t('builds.list.subtitle') }}</p>
        </div>
        <div class="workspace-command-actions">
          <RouterLink class="button-box primary-action" to="/builds/new">{{ t('builds.list.newBuild') }}</RouterLink>
        </div>
      </header>

      <section class="build-library-toolbar" :aria-label="t('discovery.builds.toolbarLabel')">
        <label class="build-library-control">
          <AppIcon name="compass" :size="19" />
          <input v-model="search" type="search" :placeholder="t('builds.list.searchPlaceholder')" />
        </label>
        <label class="build-library-control">
          <select v-model="buildType">
            <option v-for="option in buildTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <button type="button" :disabled="!hasActiveDiscovery" @click="resetDiscovery">{{ t('discovery.reset') }}</button>
        <button type="button" @click="showAllBuilds">{{ t('discovery.builds.showAll') }}</button>
      </section>

      <BuildDiscoveryRail
        id="build-discovery"
        v-model="classification"
        :groups="discoveryGroups"
        :title="t('discovery.builds.title')"
        :hint="t('discovery.builds.hint')"
      />

      <section v-if="hasActiveDiscovery" class="build-library-results" aria-live="polite">
        <div class="workspace-section-title build-library-results-heading">
          <div><h2>{{ selectedDiscoveryLabel }}</h2></div>
          <span class="build-library-count">{{ buildCountLabel }}</span>
        </div>
        <p v-if="loading" class="muted table-state">{{ t('builds.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="buildRows.length === 0" class="muted table-state">{{ t('builds.list.empty') }}</p>
        <BuildResultTable v-else :rows="buildRows" :labels="resultLabels" />
      </section>
    </div>
  </section>
</template>
