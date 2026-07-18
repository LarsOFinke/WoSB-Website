<script setup>
import { computed, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import DiscoveryTileGrid from '@/core/components/DiscoveryTileGrid.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listGuides } from '@/modules/guides/api/guides'
import { localizedGuideDiscoveryGroups } from '@/modules/guides/domain/guideDiscovery'

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
const summary = computed(() => guides.value.length === 1 ? t('guides.list.summaryOne') : t('guides.list.summaryMany', { count: guides.value.length }))
const selectedCategoryLabel = computed(() => discoveryGroups.value.flatMap((group) => group.items).find((item) => item.value === category.value)?.label || t('discovery.guides.allResults'))
function categoryLabel(value) { return t(`guides.categories.${value || 'general'}`) }
async function loadGuides() {
  if (!hasActiveDiscovery.value) { guides.value = []; return }
  loading.value = true; error.value = ''
  try { guides.value = await listGuides(search.value, category.value) }
  catch (err) { error.value = err.message || t('guides.list.loadError') }
  finally { loading.value = false }
}
function resetDiscovery() { search.value = ''; category.value = ''; showAll.value = false; guides.value = []; error.value = '' }
function showAllGuides() { showAll.value = true; category.value = ''; loadGuides() }
watch([search, category], () => { showAll.value = false; window.clearTimeout(searchTimer); searchTimer = window.setTimeout(loadGuides, 220) })
</script>

<template>
  <section class="guides-page discovery-page" aria-labelledby="guides-title">
    <div class="wire-frame page-frame compact-frame guides-frame discovery-frame">
      <header class="wire-section build-list-hero guides-hero discovery-hero">
        <div><p class="eyebrow">{{ t('common.guides') }}</p><h1 id="guides-title">{{ t('guides.list.title') }}</h1><p>{{ t('guides.list.subtitle') }}</p></div>
        <RouterLink class="button-box primary-action" :to="isAuthenticated ? '/guides/new' : '/login'">{{ t(isAuthenticated ? 'guides.list.newGuide' : 'guides.list.loginToCreate') }}</RouterLink>
      </header>
      <section class="wire-section discovery-toolbar">
        <label class="filter-box search-filter-box"><AppIcon name="guides" /><input v-model="search" type="search" :placeholder="t('guides.list.searchPlaceholder')" /></label>
        <button type="button" class="discovery-reset" :disabled="!hasActiveDiscovery" @click="resetDiscovery">{{ t('discovery.reset') }}</button>
      </section>
      <section class="wire-section discovery-picker guide-discovery-picker" aria-labelledby="guide-discovery-title">
        <div class="discovery-section-heading"><div><p class="eyebrow">{{ t('discovery.chooseFirst') }}</p><h2 id="guide-discovery-title">{{ t('discovery.guides.title') }}</h2><p>{{ t('discovery.guides.hint') }}</p></div></div>
        <div v-for="group in discoveryGroups" :key="group.key" class="discovery-group guide-discovery-group">
          <h3>{{ group.label }}</h3><DiscoveryTileGrid v-model="category" :items="group.items" />
        </div>
        <button type="button" class="discovery-show-all" @click="showAllGuides"><AppIcon name="compass" /><span><strong>{{ t('discovery.guides.showAll') }}</strong><small>{{ t('discovery.guides.showAllHint') }}</small></span><AppIcon name="arrow-right" /></button>
      </section>
      <section v-if="hasActiveDiscovery" class="wire-section filter-table guides-results-panel discovery-results" aria-live="polite">
        <div class="discovery-results-heading"><div><p class="eyebrow">{{ t('discovery.results') }}</p><h2>{{ selectedCategoryLabel }}</h2></div><span class="summary-pill">{{ summary }}</span></div>
        <p v-if="loading" class="muted table-state">{{ t('guides.list.loading') }}</p><p v-else-if="error" class="error-text table-state">{{ error }}</p><p v-else-if="guides.length === 0" class="muted table-state">{{ t('guides.list.empty') }}</p>
        <div v-else class="build-card-list refined-card-list guides-card-list"><RouterLink v-for="guide in guides" :key="guide.id" class="build-list-card refined-build-card guide-list-card" :to="`/guides/${guide.id}`"><div class="build-card-main"><div><strong>{{ guide.title }}</strong><span>{{ categoryLabel(guide.category) }} · {{ t('guides.list.by', { name: guide.owner.display_name }) }}</span></div><div class="guide-list-pills"><span class="type-pill">{{ t('guides.list.attachments', { count: guide.attachment_count }) }}</span><span v-if="guide.build_reference_count" class="type-pill">{{ t('buildEmbeds.referenceCount', { count: guide.build_reference_count }) }}</span></div></div><p class="group-card-description">{{ guide.summary || t('guides.list.noSummary') }}</p></RouterLink></div>
      </section>
    </div>
  </section>
</template>
