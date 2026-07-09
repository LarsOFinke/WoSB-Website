<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listGroups } from '@/services/groups'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { isAuthenticated } = useSession()

const groups = ref([])
const search = ref('')
const focus = ref('')
const maxShipRate = ref('')
const minShipRate = ref('')
const loading = ref(false)
const error = ref('')
let searchTimer = null

const rateOptions = [7, 6, 5, 4, 3, 2, 1]

const focusOptions = computed(() => [
  { value: '', label: t('groups.focus.all') },
  { value: 'pve_farming', label: t('focus.pve_farming') },
  { value: 'pve_imp_hunting', label: t('focus.pve_imp_hunting') },
  { value: 'pve_general', label: t('focus.pve_general') },
  { value: 'pvp_open_world', label: t('focus.pvp_open_world') },
  { value: 'pvp_arena', label: t('focus.pvp_arena') },
  { value: 'pvp_general', label: t('focus.pvp_general') },
  { value: 'trading', label: t('focus.trading') },
  { value: 'other', label: t('focus.other') },
])

const groupCountLabel = computed(() =>
  groups.value.length === 1 ? t('groups.list.summaryOne') : t('groups.list.summaryMany', { count: groups.value.length }),
)

const rateRangeInvalid = computed(() =>
  minShipRate.value && maxShipRate.value && Number(maxShipRate.value) > Number(minShipRate.value),
)

function rateRequirement(group) {
  if (group.min_ship_rate && group.max_ship_rate) {
    return t('groups.list.rateRange', { max: group.max_ship_rate, min: group.min_ship_rate })
  }
  if (group.min_ship_rate) return t('groups.list.minRate', { value: group.min_ship_rate })
  if (group.max_ship_rate) return t('groups.list.maxRate', { value: group.max_ship_rate })
  return t('groups.detail.anyRate')
}

function formatSchedule(group) {
  if (!group.scheduled_start_at) return t('groups.detail.noSchedule')
  const start = new Date(group.scheduled_start_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  if (!group.scheduled_end_at) return start
  const end = new Date(group.scheduled_end_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  return `${start} – ${end}`
}

function groupMeta(group) {
  const parts = [t(`focus.${group.focus}`)]
  if (group.scheduled_start_at) parts.push(formatSchedule(group))
  if (group.min_ship_rate || group.max_ship_rate) parts.push(rateRequirement(group))
  return parts.join(' · ')
}

async function loadGroups() {
  if (rateRangeInvalid.value) {
    groups.value = []
    error.value = t('groups.list.rateFilterInvalid')
    return
  }

  loading.value = true
  error.value = ''
  try {
    groups.value = await listGroups({
      search: search.value,
      focus: focus.value,
      minShipRate: minShipRate.value,
      maxShipRate: maxShipRate.value,
    })
  } catch (err) {
    error.value = err.message || t('groups.list.loadError')
  } finally {
    loading.value = false
  }
}

watch([search, focus, minShipRate, maxShipRate], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadGroups, 220)
})

onMounted(loadGroups)
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
