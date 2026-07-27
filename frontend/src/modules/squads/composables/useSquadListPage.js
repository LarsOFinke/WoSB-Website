import { computed, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listSquads } from '@/modules/squads/api/squads'

export function useSquadListPage() {
  const { t } = useLocale()
  const { canManageFleet } = useSession()

  const squads = ref([])
  const loading = ref(false)
  const error = ref('')
  const includeInactive = ref(false)

  const activeSquads = computed(() => squads.value.filter((squad) => squad.is_active))
  const mySquads = computed(() => activeSquads.value.filter((squad) => squad.is_member))
  const managedSquads = computed(() => activeSquads.value.filter((squad) => squad.can_manage))

  async function loadSquads() {
    loading.value = true
    error.value = ''
    try {
      squads.value = await listSquads({ includeInactive: includeInactive.value && canManageFleet.value })
    } catch (err) {
      error.value = err.message || t('squads.list.loadError')
    } finally {
      loading.value = false
    }
  }

  watch(includeInactive, loadSquads)
  onMounted(loadSquads)

  return {
    t,
    canManageFleet,
    squads,
    loading,
    error,
    includeInactive,
    activeSquads,
    mySquads,
    managedSquads,
    loadSquads,
  }
}
