import { onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { deleteStrategy, listStrategies } from '../api/strategies.js'
import { strategyShareUrl } from '../domain/strategyDocument.js'

export function useStrategyListPage() {
  const { t } = useLocale()
  const { canAuthorContent } = useSession()
  const strategies = ref([])
  const loading = ref(false)
  const error = ref('')

  async function load() {
    loading.value = true
    try { strategies.value = await listStrategies() }
    catch (exception) { error.value = exception.message || t('strategyPlanner.loadError') }
    finally { loading.value = false }
  }

  async function remove(item) {
    if (!window.confirm(t('strategyPlanner.confirmDelete'))) return
    await deleteStrategy(item.id)
    await load()
  }

  async function copy(item) {
    await navigator.clipboard.writeText(strategyShareUrl(item.public_id))
  }

  onMounted(load)
  return { t, canAuthorContent, strategies, loading, error, remove, copy }
}
