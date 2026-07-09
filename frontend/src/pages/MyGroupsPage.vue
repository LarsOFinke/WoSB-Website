<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { closeGroup, listMyGroups } from '@/services/groups'

const { t } = useLocale()
const groups = ref([])
const search = ref('')
const loading = ref(false)
const error = ref('')
const pendingCloseId = ref(null)
let searchTimer = null

const countLabel = computed(() =>
  groups.value.length === 1 ? t('myGroups.summaryOne') : t('myGroups.summaryMany', { count: groups.value.length }),
)

async function loadGroups() {
  loading.value = true
  error.value = ''
  try {
    groups.value = await listMyGroups(search.value)
  } catch (err) {
    error.value = err.message || t('myGroups.loadError')
  } finally {
    loading.value = false
  }
}

async function confirmClose(groupId) {
  error.value = ''
  try {
    await closeGroup(groupId)
    pendingCloseId.value = null
    await loadGroups()
  } catch (err) {
    error.value = err.message || t('myGroups.closeError')
  }
}

watch(search, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadGroups, 220)
})

onMounted(loadGroups)
</script>

<template>
  <section class="my-groups-page" aria-labelledby="my-groups-title">
    <div class="wire-frame page-frame compact-frame my-groups-frame">
      <header class="wire-section build-list-hero groups-hero">
        <div>
          <p class="eyebrow">{{ t('myGroups.eyebrow') }}</p>
          <h1 id="my-groups-title">{{ t('myGroups.title') }}</h1>
          <p>{{ t('myGroups.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ countLabel }}</span>
          <RouterLink class="button-box primary-action" to="/groups/new">{{ t('myGroups.create') }}</RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel">
        <div>
          <h2>{{ t('myGroups.manageTitle') }}</h2>
          <p>{{ t('myGroups.manageText') }}</p>
        </div>
        <label class="filter-box admin-search">
          <input v-model="search" type="search" :placeholder="t('myGroups.searchPlaceholder')" />
        </label>
      </section>

      <section class="wire-section filter-table group-results-panel">
        <p v-if="loading" class="muted table-state">{{ t('myGroups.loading') }}</p>
        <p v-else-if="error" class="error-text table-state">{{ error }}</p>
        <p v-else-if="groups.length === 0" class="muted table-state">{{ t('myGroups.emptyText') }}</p>

        <div v-else class="admin-build-list my-group-list">
          <article v-for="group in groups" :key="group.id" class="admin-build-row my-group-row">
            <RouterLink class="admin-build-main" :to="`/groups/${group.id}`">
              <strong>{{ group.title }}</strong>
              <span>
                {{ t(`focus.${group.focus}`) }} · {{ t('groups.list.announcementMode') }} ·
                {{ t(`groups.status.${group.status}`) }}
              </span>
            </RouterLink>

            <div v-if="pendingCloseId === group.id" class="delete-confirmation">
              <span>{{ t('myGroups.confirmClose') }}</span>
              <button class="danger-action" type="button" @click="confirmClose(group.id)">{{ t('myGroups.closeNow') }}</button>
              <button class="small-action" type="button" @click="pendingCloseId = null">{{ t('common.cancel') }}</button>
            </div>

            <button v-else class="danger-action" type="button" :disabled="group.status === 'closed'" @click="pendingCloseId = group.id">
              {{ t('myGroups.close') }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
