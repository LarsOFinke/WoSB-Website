import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listBuilds } from '@/modules/builds/api/builds'
import { absoluteFileUrl } from '@/modules/files/api/files'
import { listGuides } from '@/modules/guides/api/guides'
import { listShips } from '@/modules/ships/api/ships'
import { getSharedStrategy, getStrategy } from '../api/strategies.js'
import { emptyStrategyDocument, parseStrategyDocument, strategyShareUrl } from '../domain/strategyDocument.js'
import { downloadStrategySvg } from '../strategySvgExport.js'

export function useStrategyViewPage() {
  const route = useRoute()
  const { t } = useLocale()
  const { canAuthorContent, user } = useSession()
  const strategy = ref(null)
  const document = ref(emptyStrategyDocument())
  const ships = ref([])
  const builds = ref([])
  const guides = ref([])
  const canvas = ref(null)
  const loading = ref(true)
  const error = ref('')

  const publicId = computed(() => String(route.params.publicId || ''))
  const strategyId = computed(() => Number(route.params.id || 0))
  const isShared = computed(() => Boolean(publicId.value))
  const canEdit = computed(() => Boolean(canAuthorContent.value && strategy.value && user.value
    && Number(strategy.value.owner_id) === Number(user.value.id)))
  const backgroundUrl = computed(() => absoluteFileUrl(strategy.value?.background_file?.public_url || ''))
  const shareUrl = computed(() => strategy.value?.is_published && strategy.value?.public_id
    ? strategyShareUrl(strategy.value.public_id) : '')

  async function loadCatalogs() {
    if (!user.value) return
    const results = await Promise.allSettled([
      listShips(), listBuilds('', '', '', 100, 0), listGuides('', '', 100, 0),
    ])
    if (results[0].status === 'fulfilled') ships.value = results[0].value || []
    if (results[1].status === 'fulfilled') builds.value = results[1].value?.items || []
    if (results[2].status === 'fulfilled') guides.value = results[2].value || []
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      const request = isShared.value ? getSharedStrategy(publicId.value) : getStrategy(strategyId.value)
      const [value] = await Promise.all([request, loadCatalogs()])
      strategy.value = value
      document.value = parseStrategyDocument(value.overlay_json)
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.loadError')
    } finally {
      loading.value = false
    }
  }

  async function copyShareLink() {
    if (shareUrl.value) await navigator.clipboard.writeText(shareUrl.value)
  }

  async function downloadSvg() {
    const source = canvas.value?.element
    if (!source) return
    error.value = ''
    try {
      await downloadStrategySvg(source, backgroundUrl.value, strategy.value?.title)
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.exportError')
    }
  }

  onMounted(load)
  return {
    t, strategy, document, ships, builds, guides, canvas, loading, error,
    isShared, canEdit, backgroundUrl, shareUrl, copyShareLink, downloadSvg,
    printStrategy: () => window.print(),
  }
}
