import { computed, ref } from 'vue'

import { deleteAdminBuild, listAdminBuilds } from '@/modules/admin/api/admin'
import { filterAdminBuilds } from '@/modules/admin/domain/adminWorkspace'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

export function useAdminBuilds({ isStaff, t, clearConfirmation }) {
  const builds = ref([])
  const search = ref('')
  const buildType = ref('')
  const buildRate = ref('')
  const buildVisibility = ref('')
  const loading = ref(false)
  const error = ref('')

  const filteredBuilds = computed(() => filterAdminBuilds(builds.value, {
    rate: buildRate.value,
    visibility: buildVisibility.value,
  }))
  const buildRates = computed(() => [...new Set(builds.value
    .map((build) => build.ship?.rate)
    .filter((rate) => rate !== null && rate !== undefined))]
    .sort((left, right) => Number(left) - Number(right)))
  const buildCountLabel = computed(() => filteredBuilds.value.length === 1
    ? t('admin.builds.summaryOne')
    : t('admin.builds.summaryMany', { count: filteredBuilds.value.length }))

  async function loadBuilds() {
    if (!isStaff.value) return
    loading.value = true
    error.value = ''
    try {
      builds.value = await listAdminBuilds(search.value, buildType.value)
    } catch (err) {
      error.value = err.message || t('admin.builds.loadError')
    } finally {
      loading.value = false
    }
  }

  async function confirmDeleteBuild(buildId) {
    error.value = ''
    try {
      await deleteAdminBuild(buildId)
      clearConfirmation()
      await loadBuilds()
    } catch (err) {
      error.value = err.message || t('admin.builds.deleteError')
    }
  }

  function resetBuildFilters() {
    search.value = ''
    buildType.value = ''
    buildRate.value = ''
    buildVisibility.value = ''
  }

  useDebouncedWatch([search, buildType], loadBuilds, 220)

  return {
    builds, search, buildType, buildRate, buildVisibility, loading, error,
    filteredBuilds, buildRates, buildCountLabel,
    loadBuilds, confirmDeleteBuild, resetBuildFilters,
  }
}
