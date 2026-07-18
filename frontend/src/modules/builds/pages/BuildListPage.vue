<script setup>
import { computed, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import DiscoveryTileGrid from '@/core/components/DiscoveryTileGrid.vue'
import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'
import { localizedBuildDiscoveryGroups } from '@/modules/builds/domain/buildDiscovery'

const { optionLabel, t } = useLocale()
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

function buildTypeLabel(value) { return buildTypeLabels.value[value] || value || t('builds.types.balanced') }
function crewTotal(build) { return build.sailors + build.soldiers + build.musketeers + build.mercenaries }
function slotSummary(build) {
  const stats = build.ship_stats || {}
  const used = stats.upgrade_slots_used ?? [1,2,3,4,5,6,7,8].filter((index) => build[`upgrade_${index}`]).length
  return t('builds.list.upgradeSummary', { used, max: stats.upgrade_slots_available || 5 })
}
function inventorySummary(build) {
  const stats = build.ship_stats || {}
  return t('builds.list.inventorySummary', { ammo: stats.ammunition_slots_used ?? build.ammunition_slots?.length ?? 0, consumables: stats.consumable_slots_used ?? build.consumable_slots?.length ?? 0, hold: stats.hold_slots_used ?? build.hold_slots?.length ?? 0 })
}
function weaponSummary(build) { return t('builds.list.weaponSummary', { count: build.ship_stats?.weapon_total || 0 }) }
function specialCrewSummary(build) { return t('builds.list.specialCrewSummary', { count: build.ship_stats?.special_crew_total || 0 }) }
function classificationLabel(value) {
  return discoveryGroups.value.flatMap((group) => group.items).find((item) => item.value === value)?.label || value
}
function slotLabel(slot) {
  if (typeof slot === 'string') return optionLabel(slot)
  return slot?.item ? `${optionLabel(slot.item)} ×${slot.quantity || 1}` : ''
}
function previewItems(items) {
  const labels = (items || []).map(slotLabel).filter(Boolean)
  return labels.length ? `${labels.slice(0, 2).join(', ')}${labels.length > 2 ? ' …' : ''}` : t('builds.list.noSlots')
}
function specialistPreview(items) {
  const labels = (items || []).map((slot) => optionLabel(typeof slot === 'string' ? slot : slot?.item)).filter(Boolean)
  return labels.length ? `${labels.slice(0, 2).join(', ')}${labels.length > 2 ? ' …' : ''}` : t('builds.list.noSlots')
}

async function loadBuilds() {
  if (!hasActiveDiscovery.value) { builds.value = []; return }
  loading.value = true
  error.value = ''
  try { builds.value = await listBuilds(search.value, buildType.value, classification.value) }
  catch (err) { error.value = err.message || t('builds.list.loadError') }
  finally { loading.value = false }
}
function resetDiscovery() {
  search.value = ''
  buildType.value = ''
  classification.value = ''
  showAll.value = false
  builds.value = []
  error.value = ''
}
function showAllBuilds() { showAll.value = true; classification.value = ''; loadBuilds() }

watch([search, buildType, classification], () => {
  showAll.value = false
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})
</script>

<template>
  <section class="build-list-page discovery-page" aria-labelledby="builds-title">
    <div class="wire-frame page-frame compact-frame build-list-frame discovery-frame">
      <header class="wire-section build-list-hero discovery-hero">
        <div><p class="eyebrow">{{ t('common.builds') }}</p><h1 id="builds-title">{{ t('builds.list.title') }}</h1><p>{{ t('builds.list.subtitle') }}</p></div>
        <RouterLink class="button-box primary-action" to="/builds/new">{{ t('builds.list.newBuild') }}</RouterLink>
      </header>

      <section class="wire-section discovery-toolbar" :aria-label="t('discovery.builds.toolbarLabel')">
        <label class="filter-box search-filter-box"><AppIcon name="compass" /><input v-model="search" type="search" :placeholder="t('builds.list.searchPlaceholder')" /></label>
        <label class="filter-box type-filter-box"><select v-model="buildType"><option v-for="option in buildTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option></select></label>
        <button type="button" class="discovery-reset" :disabled="!hasActiveDiscovery" @click="resetDiscovery">{{ t('discovery.reset') }}</button>
      </section>

      <section class="wire-section discovery-picker" aria-labelledby="build-discovery-title">
        <div class="discovery-section-heading"><div><p class="eyebrow">{{ t('discovery.chooseFirst') }}</p><h2 id="build-discovery-title">{{ t('discovery.builds.title') }}</h2><p>{{ t('discovery.builds.hint') }}</p></div></div>
        <div v-for="group in discoveryGroups" :key="group.key" class="discovery-group">
          <h3>{{ group.label }}</h3>
          <DiscoveryTileGrid v-model="classification" :items="group.items" compact />
        </div>
        <button type="button" class="discovery-show-all" @click="showAllBuilds"><AppIcon name="compass" /><span><strong>{{ t('discovery.builds.showAll') }}</strong><small>{{ t('discovery.builds.showAllHint') }}</small></span><AppIcon name="arrow-right" /></button>
      </section>

      <section v-if="hasActiveDiscovery" class="wire-section filter-table build-results-panel discovery-results" aria-live="polite">
        <div class="discovery-results-heading"><div><p class="eyebrow">{{ t('discovery.results') }}</p><h2>{{ selectedDiscoveryLabel }}</h2></div><span class="summary-pill">{{ buildCountLabel }}</span></div>
        <p v-if="loading" class="muted table-state">{{ t('builds.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="builds.length === 0" class="muted table-state">{{ t('builds.list.empty') }}</p>
        <div v-else class="build-card-list refined-card-list">
          <RouterLink v-for="build in builds" :key="build.id" class="build-list-card refined-build-card" :to="`/builds/${build.id}`">
            <div class="build-card-main"><div><strong>{{ build.build_name }}</strong><span>{{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ build.ship.ship_type }}</span></div><span class="type-pill">{{ buildTypeLabel(build.build_type) }}</span></div>
            <div v-if="build.classification_tags?.length" class="classification-chip-row"><span v-for="tag in build.classification_tags" :key="tag">{{ classificationLabel(tag) }}</span></div>
            <div class="build-card-meta refined-meta"><span>{{ t('builds.list.crew', { current: crewTotal(build), max: build.ship_stats?.crew_capacity || build.ship.crew_capacity }) }}</span><span>{{ slotSummary(build) }}</span><span>{{ weaponSummary(build) }}</span><span>{{ specialCrewSummary(build) }}</span><span>{{ inventorySummary(build) }}</span></div>
            <div class="build-card-preview refined-preview"><span>{{ t('builds.list.weaponPreview', { items: previewItems([...(build.front_weapon_slots || []), ...(build.port_weapon_slots || []), ...(build.starboard_weapon_slots || [])]) }) }}</span><span>{{ t('builds.list.specialCrewPreview', { items: specialistPreview(build.special_crew_slots) }) }}</span></div>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
