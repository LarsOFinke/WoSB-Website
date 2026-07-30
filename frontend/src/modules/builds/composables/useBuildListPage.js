import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { listBuilds, listBuildRoles } from '@/modules/builds/api/builds'
import { localizedBuildDiscoveryGroups } from '@/modules/builds/domain/buildDiscovery'

export function useBuildListPage() {
  const { t } = useLocale()
  const builds = ref([])
  const roles = ref([])
  const search = ref('')
  const buildType = ref('')
  const classification = ref('')
  const showAll = ref(true)
  const loading = ref(false)
  const total = ref(0)
  const limit = 50
  const offset = ref(0)
  const error = ref('')
  let searchTimer = null

  const discoveryGroups = computed(() => localizedBuildDiscoveryGroups(t))
  const hasFilters = computed(() => Boolean(search.value.trim() || buildType.value || classification.value))
  const hasActiveDiscovery = computed(() => showAll.value || hasFilters.value)
  const buildTypeOptions = computed(() => [
    { value: '', label: t('builds.types.all') },
    ...roles.value.map((role) => ({ value: role.slug, label: role.label })),
  ])
  const buildTypeLabels = computed(() => Object.fromEntries(buildTypeOptions.value.map((option) => [option.value, option.label])))
  const buildCountLabel = computed(() => total.value === 1
    ? t('builds.list.summaryOne')
    : t('builds.list.summaryMany', { count: total.value }))
  const pageNumber = computed(() => Math.floor(offset.value / limit) + 1)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / limit)))
  const canGoPrevious = computed(() => offset.value > 0)
  const canGoNext = computed(() => offset.value + limit < total.value)
  const selectedDiscoveryLabel = computed(() => {
    const item = discoveryGroups.value.flatMap((group) => group.items).find(({ value }) => value === classification.value)
    return item?.label || t('discovery.builds.allResults')
  })
  const resultLabels = computed(() => ({
    results: t('discovery.results'),
    build: t('common.builds'),
    type: t('common.type'),
    crew: t('common.crew'),
    upgrades: t('common.upgrades'),
    weapons: t('builds.create.sections.weapons'),
    specialists: t('builds.create.sections.specialCrew'),
    inventory: t('builds.create.sections.inventory'),
    upvotes: t('builds.voting.upvotes'),
  }))
  const buildRows = computed(() => builds.value.map((build) => {
    const metrics = build.metrics || {}
    const usedUpgrades = metrics.upgrade_slots_used || 0
    const crew = metrics.crew_total || 0
    return {
      id: build.id,
      name: build.build_name,
      ship: [build.ship?.name, build.ship?.rate ? `${t('common.rate')} ${build.ship.rate}` : '', build.ship?.ship_type].filter(Boolean).join(' · '),
      type: build.build_role_label || buildTypeLabels.value[build.build_type] || build.build_type || t('builds.types.balanced'),
      crew: t('builds.list.crew', { current: crew, max: metrics.crew_capacity || build.ship?.crew_capacity || 0 }),
      upgrades: t('builds.list.upgradeSummary', { used: usedUpgrades, max: metrics.upgrade_slots_available || 0 }),
      weapons: t('builds.list.weaponSummary', { count: metrics.weapon_total || 0 }),
      specialists: t('builds.list.specialCrewSummary', { count: metrics.special_crew_total || 0 }),
      upvotes: Number(build.upvote_count || 0),
      inventory: t('builds.list.inventorySummary', {
        ammo: metrics.ammunition_slots_used || 0,
        consumables: metrics.consumable_slots_used || 0,
        hold: metrics.hold_slots_used || 0,
      }),
    }
  }))

  async function loadBuilds() {
    if (!hasActiveDiscovery.value) {
      builds.value = []
      return
    }
    loading.value = true
    error.value = ''
    try {
      const [nextBuilds, nextRoles] = await Promise.all([
        listBuilds(search.value, buildType.value, classification.value, limit, offset.value),
        roles.value.length ? Promise.resolve(roles.value) : listBuildRoles(),
      ])
      builds.value = nextBuilds.items || []
      total.value = Number(nextBuilds.total || 0)
      roles.value = nextRoles
    } catch (err) {
      error.value = err.message || t('builds.list.loadError')
    } finally {
      loading.value = false
    }
  }

  function resetDiscovery() {
    offset.value = 0
    const hadFilters = hasFilters.value
    search.value = ''
    buildType.value = ''
    classification.value = ''
    showAll.value = true
    error.value = ''
    window.clearTimeout(searchTimer)
    if (!hadFilters) void loadBuilds()
  }

  async function goToPage(direction) {
    const nextOffset = Math.max(0, offset.value + direction * limit)
    if (nextOffset === offset.value || nextOffset >= total.value) return
    offset.value = nextOffset
    await loadBuilds()
  }

  function showAllBuilds() {
    resetDiscovery()
  }

  watch([search, buildType, classification], () => {
    offset.value = 0
    showAll.value = !hasFilters.value
    window.clearTimeout(searchTimer)
    searchTimer = window.setTimeout(loadBuilds, 220)
  })

  onMounted(loadBuilds)
  onBeforeUnmount(() => window.clearTimeout(searchTimer))

  return {
    t,
    builds,
    roles,
    search,
    buildType,
    classification,
    showAll,
    loading,
    error,
    total,
    offset,
    searchTimer,
    discoveryGroups,
    hasFilters,
    hasActiveDiscovery,
    buildTypeOptions,
    buildTypeLabels,
    buildCountLabel,
    pageNumber,
    pageCount,
    canGoPrevious,
    canGoNext,
    selectedDiscoveryLabel,
    resultLabels,
    buildRows,
    loadBuilds,
    resetDiscovery,
    showAllBuilds,
    goToPage,
    localizedBuildDiscoveryGroups,
  }
}
