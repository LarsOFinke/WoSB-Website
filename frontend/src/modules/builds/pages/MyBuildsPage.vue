<script setup>
import { useMyBuildsPage } from '@/modules/builds/composables/useMyBuildsPage'

const {
  optionLabel,
  t,
  builds,
  search,
  buildType,
  shipRate,
  loading,
  error,
  pendingDeleteId,
  sharedBuildId,
  shareError,
  searchTimer,
  buildTypeOptions,
  shipRateOptions,
  buildCountLabel,
  pageNumber,
  pageCount,
  canGoPrevious,
  canGoNext,
  slotLabel,
  previewItems,
  loadMyBuilds,
  goToPage,
  shareBuild,
  confirmDelete,
  copyBuildShareLink,
} = useMyBuildsPage()
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
          <label class="filter-box type-filter-box">
            <select v-model="shipRate" :aria-label="t('common.rate')">
              <option v-for="option in shipRateOptions" :key="option.value" :value="option.value">
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

        <p v-if="shareError" class="error-text table-state">{{ shareError }}</p>
        <div v-else class="my-build-list">
          <article v-for="build in builds" :key="build.id" class="my-build-row">
            <RouterLink class="my-build-row-main" :to="`/builds/${build.id}`">
              <strong>{{ build.build_name }}</strong>
              <span>
                {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} ·
                {{ build.build_role_label || build.build_type }} ·
                ▲ {{ build.upvote_count || 0 }} ·
                {{ t('builds.list.crew', { current: build.metrics?.crew_total || 0, max: build.metrics?.crew_capacity || build.ship.crew_capacity }) }}
              </span>
              <small>
                {{ t('builds.list.ammunitionPreview', { items: previewItems(build.ammunition_slots) }) }} ·
                {{ t('builds.list.holdPreview', { items: previewItems(build.hold_slots) }) }}
              </small>
            </RouterLink>

            <div class="my-build-row-actions">
              <button class="small-action" type="button" @click="shareBuild(build.id)">{{ sharedBuildId === build.id ? t('builds.share.copied') : t('builds.share.action') }}</button>
              <RouterLink class="small-action" :to="`/builds/${build.id}/edit`">
                {{ t('builds.edit.action') }}
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
            </div>
          </article>
        </div>
        <nav v-if="pageCount > 1" class="build-pagination" :aria-label="t('common.pagination')">
          <button type="button" :disabled="loading || !canGoPrevious" @click="goToPage(-1)">{{ t('common.previous') }}</button>
          <span>{{ t('common.pageOf', { page: pageNumber, pages: pageCount }) }}</span>
          <button type="button" :disabled="loading || !canGoNext" @click="goToPage(1)">{{ t('common.next') }}</button>
        </nav>
      </section>
    </div>
  </section>
</template>
