import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { closeGroup, listMyGroups } from '@/modules/groups/api/groups'

export function useMyGroupsPage() {
  const { t } = useLocale()
  const { canAuthorContent } = useSession()
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
    canAuthorContent,
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
