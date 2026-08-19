<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import BuildDiscoveryRail from '@/modules/builds/components/BuildDiscoveryRail.vue'
import BuildResultTable from '@/modules/builds/components/BuildResultTable.vue'
import '@/styles/workspaceRefresh.css'
import '@/modules/builds/styles/buildLibrary.css'
import { useBuildListPage } from '@/modules/builds/composables/useBuildListPage'

const {
  t,
  canAuthorContent,
  search,
  buildType,
  shipRate,
  classification,
  loading,
  error,
  discoveryGroups,
  hasFilters,
  hasActiveDiscovery,
  buildTypeOptions,
  shipRateOptions,
  buildCountLabel,
  pageNumber,
  pageCount,
  canGoPrevious,
  canGoNext,
  selectedDiscoveryLabel,
  resultLabels,
  buildRows,
  resetDiscovery,
  showAllBuilds,
  goToPage,
} = useBuildListPage()
</script>

<template>
  <section class="build-library-page" aria-labelledby="builds-title">
    <div class="wire-frame page-frame workspace-refresh-frame build-library-frame">
      <header class="workspace-command-header">
        <div>
          <h1 id="builds-title">{{ t('builds.list.title') }}</h1>
          <p>{{ t('builds.list.subtitle') }}</p>
        </div>
        <div class="workspace-command-actions">
          <RouterLink v-if="canAuthorContent" class="button-box primary-action" to="/builds/new">{{ t('builds.list.newBuild') }}</RouterLink>
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
        <label class="build-library-control">
          <select v-model="shipRate" :aria-label="t('common.rate')">
            <option v-for="option in shipRateOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <button type="button" :disabled="!hasFilters" @click="resetDiscovery">{{ t('discovery.reset') }}</button>
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
        <nav v-if="pageCount > 1" class="build-pagination" :aria-label="t('common.pagination')">
          <button type="button" :disabled="loading || !canGoPrevious" @click="goToPage(-1)">{{ t('common.previous') }}</button>
          <span>{{ t('common.pageOf', { page: pageNumber, pages: pageCount }) }}</span>
          <button type="button" :disabled="loading || !canGoNext" @click="goToPage(1)">{{ t('common.next') }}</button>
        </nav>
      </section>
    </div>
  </section>
</template>
