import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { listThreads } from '@/modules/forum/api/forum'
import { useSession } from '@/modules/accounts/session'

export function useForumListPage() {
  const { t } = useLocale()
  const { isAuthenticated } = useSession()

  const threads = ref([])
  const search = ref('')
  const category = ref('')
  const loading = ref(false)
  const error = ref('')
  let searchTimer = null

  const categories = computed(() => [
    { value: '', label: t('forum.categories.all') },
    { value: 'general', label: t('forum.categories.general') },
    { value: 'builds', label: t('forum.categories.builds') },
    { value: 'events', label: t('forum.categories.events') },
    { value: 'support', label: t('forum.categories.support') },
    { value: 'training', label: t('forum.categories.training') },
    { value: 'logistics', label: t('forum.categories.logistics') },
  ])

  const summary = computed(() => threads.value.length === 1 ? t('forum.list.summaryOne') : t('forum.list.summaryMany', { count: threads.value.length }))

  function normalizeForumCategory(value) {
    const normalized = String(value || 'general').trim().toLowerCase()
    if (normalized === 'loistics' || normalized === 'logistic') return 'logistics'
    return normalized || 'general'
  }

  function categoryLabel(value) {
    return t(`forum.categories.${normalizeForumCategory(value)}`)
  }

  function formatDate(value) {
    return value ? new Date(value).toLocaleString() : '—'
  }

  async function loadThreads() {
    loading.value = true
    error.value = ''
    try {
      threads.value = await listThreads(search.value, category.value)
    } catch (err) {
      error.value = err.message || t('forum.list.loadError')
    } finally {
      loading.value = false
    }
  }

  watch([search, category], () => {
    window.clearTimeout(searchTimer)
    searchTimer = window.setTimeout(loadThreads, 220)
  })

  onBeforeUnmount(() => window.clearTimeout(searchTimer))

  onMounted(loadThreads)

  return {
    t,
    isAuthenticated,
    threads,
    search,
    category,
    loading,
    error,
    searchTimer,
    categories,
    summary,
    normalizeForumCategory,
    categoryLabel,
    formatDate,
    loadThreads,
  }
}
