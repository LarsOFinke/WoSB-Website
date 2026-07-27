<script setup>
import { useGroupListPage } from '@/modules/groups/composables/useGroupListPage'

const {
  t,
  isAuthenticated,
  groups,
  search,
  focus,
  maxShipRate,
  minShipRate,
  loading,
  error,
  searchTimer,
  rateOptions,
  focusOptions,
  groupCountLabel,
  rateRangeInvalid,
  rateRequirement,
  formatSchedule,
  groupMeta,
  loadGroups,
} = useGroupListPage()
</script>

<template>
  <section class="groups-page" aria-labelledby="groups-title">
    <div class="wire-frame page-frame compact-frame groups-frame">
      <header class="wire-section build-list-hero groups-hero">
        <div>
          <p class="eyebrow">{{ t('common.groups') }}</p>
          <h1 id="groups-title">{{ t('groups.list.title') }}</h1>
          <p>{{ t('groups.list.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ groupCountLabel }}</span>
          <RouterLink v-if="isAuthenticated" class="button-box primary-action" to="/groups/new">
            {{ t('groups.list.newGroup') }}
          </RouterLink>
          <RouterLink v-else class="button-box primary-action" to="/login">
            {{ t('groups.list.loginToCreate') }}
          </RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel" :aria-label="t('groups.list.filtersLabel')">
        <div>
          <h2>{{ t('groups.list.filtersTitle') }}</h2>
          <p>{{ t('groups.list.filtersText') }}</p>
        </div>
        <div class="list-toolbar has-type-filter refined-toolbar group-filter-toolbar">
          <label class="filter-box search-filter-box">
            <input v-model="search" type="search" :placeholder="t('groups.list.searchPlaceholder')" />
          </label>
          <label class="filter-box type-filter-box select-shell toolbar-select-shell">
            <select v-model="focus">
              <option v-for="option in focusOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="filter-box rate-filter-box select-shell toolbar-select-shell">
            <select v-model="maxShipRate">
              <option value="">{{ t('groups.list.anyMaxRate') }}</option>
              <option v-for="rate in rateOptions" :key="`max-${rate}`" :value="rate">
                {{ t('groups.fields.maxShipRate') }} {{ rate }}
              </option>
            </select>
          </label>
          <label class="filter-box rate-filter-box select-shell toolbar-select-shell">
            <select v-model="minShipRate">
              <option value="">{{ t('groups.list.anyMinRate') }}</option>
              <option v-for="rate in rateOptions" :key="`min-${rate}`" :value="rate">
                {{ t('groups.fields.minShipRate') }} {{ rate }}
              </option>
            </select>
          </label>
        </div>
        <p class="muted filter-hint">{{ t('groups.list.rateFilterHint') }}</p>
      </section>

      <section class="wire-section filter-table group-results-panel">
        <p v-if="loading" class="muted table-state">{{ t('groups.list.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="groups.length === 0" class="muted table-state">{{ t('groups.list.empty') }}</p>

        <div v-else class="build-card-list refined-card-list group-card-list">
          <RouterLink v-for="group in groups" :key="group.id" class="build-list-card refined-build-card group-list-card" :to="`/groups/${group.id}`">
            <div class="build-card-main">
              <div>
                <strong>{{ group.title }}</strong>
                <span>{{ groupMeta(group) }}</span>
              </div>
              <span class="type-pill" :class="`status-${group.status}`">{{ t(`groups.status.${group.status}`) }}</span>
            </div>

            <div class="build-card-meta refined-meta">
              <span>{{ t('groups.list.leader', { name: group.owner.display_name }) }}</span>
              <span>{{ t('groups.list.members', { current: group.active_members_count, max: group.max_members }) }}</span>
              <span>{{ formatSchedule(group) }}</span>
              <span>{{ rateRequirement(group) }}</span>
              <span>{{ group.fleet_restriction || t('groups.list.noFleetRestriction') }}</span>
            </div>

            <p class="group-card-description">{{ group.description || t('groups.list.noDescription') }}</p>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>
