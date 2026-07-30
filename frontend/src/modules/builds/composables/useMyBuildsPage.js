import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { deleteMyBuild, listBuildRoles, listMyBuilds } from '@/modules/builds/api/builds'
import { copyBuildShareLink } from '@/modules/builds/shareBuild'

export function useMyBuildsPage() {
  const { optionLabel, t } = useLocale()

  const builds = ref([])
  const buildRoles = ref([])
  const search = ref('')
  const buildType = ref('')
  const loading = ref(false)
  const total = ref(0)
  const limit = 50
  const offset = ref(0)
  const error = ref('')
  const pendingDeleteId = ref(null)
  const sharedBuildId = ref(null)
  const shareError = ref('')
  let searchTimer = null
  let shareTimer = null

  const buildTypeOptions = computed(() => [
    { value: '', label: t('builds.types.all') },
    ...buildRoles.value.map((role) => ({ value: role.slug, label: role.label })),
  ])

  const buildCountLabel = computed(() =>
    total.value === 1 ? t('myBuilds.summaryOne') : t('myBuilds.summaryMany', { count: total.value }),
  )
  const pageNumber = computed(() => Math.floor(offset.value / limit) + 1)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / limit)))
  const canGoPrevious = computed(() => offset.value > 0)
  const canGoNext = computed(() => offset.value + limit < total.value)

  function slotLabel(slot) {
    if (typeof slot === 'string') return optionLabel(slot)
    if (!slot?.item) return ''
    return `${optionLabel(slot.item)} ×${slot.quantity || 1}`
  }

  function previewItems(items) {
    const labels = (items || []).map(slotLabel).filter(Boolean)
    if (!labels.length) return t('builds.list.noSlots')
    return labels.slice(0, 2).join(', ') + (labels.length > 2 ? ' …' : '')
  }

  async function loadMyBuilds() {
    loading.value = true
    error.value = ''
    try {
      const [nextBuilds, nextRoles] = await Promise.all([
        listMyBuilds(search.value, buildType.value, '', limit, offset.value),
        buildRoles.value.length ? Promise.resolve(buildRoles.value) : listBuildRoles(),
      ])
      builds.value = nextBuilds.items || []
      total.value = Number(nextBuilds.total || 0)
      buildRoles.value = nextRoles
    } catch (err) {
      error.value = err.message || t('myBuilds.loadError')
    } finally {
      loading.value = false
    }
  }

  async function goToPage(direction) {
    const nextOffset = Math.max(0, offset.value + direction * limit)
    if (nextOffset === offset.value || nextOffset >= total.value) return
    offset.value = nextOffset
    await loadMyBuilds()
  }

  async function shareBuild(buildId) {
    shareError.value = ''
    try {
      await copyBuildShareLink(buildId)
      sharedBuildId.value = buildId
      window.clearTimeout(shareTimer)
      shareTimer = window.setTimeout(() => {
        if (sharedBuildId.value === buildId) sharedBuildId.value = null
      }, 2200)
    } catch {
      shareError.value = t('builds.share.error')
    }
  }

  async function confirmDelete(buildId) {
    error.value = ''
    try {
      await deleteMyBuild(buildId)
      pendingDeleteId.value = null
      await loadMyBuilds()
    } catch (err) {
      error.value = err.message || t('myBuilds.deleteError')
    }
  }

  watch([search, buildType], () => {
    offset.value = 0
    window.clearTimeout(searchTimer)
    searchTimer = window.setTimeout(loadMyBuilds, 220)
  })

  onBeforeUnmount(() => {
    window.clearTimeout(searchTimer)
    window.clearTimeout(shareTimer)
  })

  onMounted(loadMyBuilds)

  return {
    optionLabel,
    t,
    builds,
    buildRoles,
    search,
    buildType,
    loading,
    error,
    total,
    offset,
    pendingDeleteId,
    sharedBuildId,
    shareError,
    searchTimer,
    buildTypeOptions,
    buildCountLabel,
    pageNumber,
    pageCount,
    canGoPrevious,
    canGoNext,
    slotLabel,
    previewItems,
    loadMyBuilds,
    goToPage,
    shareBuild,
    confirmDelete,
    copyBuildShareLink,
  }
}
