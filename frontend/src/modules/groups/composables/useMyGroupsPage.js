import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { closeGroup, listMyGroups } from '@/modules/groups/api/groups'

export function useMyGroupsPage() {
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

  onBeforeUnmount(() => window.clearTimeout(searchTimer))

  onMounted(loadGroups)

  return {
    t,
    groups,
    search,
    loading,
    error,
    pendingCloseId,
    searchTimer,
    countLabel,
    loadGroups,
    confirmClose,
  }
}
