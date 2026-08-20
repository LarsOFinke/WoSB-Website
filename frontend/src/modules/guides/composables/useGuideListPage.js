import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listGuides } from '@/modules/guides/api/guides'
import { localizedGuideDiscoveryGroups } from '@/modules/guides/domain/guideDiscovery'

export function useGuideListPage() {
  const { t } = useLocale()
  const { canAuthorContent } = useSession()
  const guides = ref([])
  const search = ref('')
  const category = ref('')
  const showAll = ref(true)
  const loading = ref(false)
  const error = ref('')
  let searchTimer = null

  const discoveryGroups = computed(() => localizedGuideDiscoveryGroups(t))
  const hasFilters = computed(() => Boolean(search.value.trim() || category.value))
  const hasActiveDiscovery = computed(() => showAll.value || hasFilters.value)
  const summary = computed(() => guides.value.length === 1
    ? t('guides.list.summaryOne')
    : t('guides.list.summaryMany', { count: guides.value.length }))
  const selectedCategoryLabel = computed(() => discoveryGroups.value
    .flatMap((group) => group.items)
    .find((item) => item.value === category.value)?.label || t('discovery.guides.allResults'))

  async function loadGuides() {
    if (!hasActiveDiscovery.value) {
      guides.value = []
      return
    }
    loading.value = true
    error.value = ''
    try {
      guides.value = await listGuides(search.value, category.value)
    } catch (err) {
      error.value = err.message || t('guides.list.loadError')
    } finally {
      loading.value = false
    }
  }

  function resetDiscovery() {
    const hadFilters = hasFilters.value
    search.value = ''
    category.value = ''
    showAll.value = true
    error.value = ''
    window.clearTimeout(searchTimer)
    if (!hadFilters) void loadGuides()
  }

  function showAllGuides() {
    resetDiscovery()
  }

  watch([search, category], () => {
    showAll.value = !hasFilters.value
    window.clearTimeout(searchTimer)
    searchTimer = window.setTimeout(loadGuides, 220)
  })

  onMounted(loadGuides)
  onBeforeUnmount(() => window.clearTimeout(searchTimer))

  return {
    t,
    canAuthorContent,
    guides,
    search,
    category,
    showAll,
    loading,
    error,
    searchTimer,
    discoveryGroups,
    hasFilters,
    hasActiveDiscovery,
    summary,
    selectedCategoryLabel,
    loadGuides,
    resetDiscovery,
    showAllGuides,
    localizedGuideDiscoveryGroups,
  }
}
