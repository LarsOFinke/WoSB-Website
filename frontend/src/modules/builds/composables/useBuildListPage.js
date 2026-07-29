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
  const buildCountLabel = computed(() => builds.value.length === 1
    ? t('builds.list.summaryOne')
    : t('builds.list.summaryMany', { count: builds.value.length }))
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
    const stats = build.ship_stats || {}
    const usedUpgrades = stats.upgrade_slots_used ?? [1, 2, 3, 4, 5, 6, 7, 8].filter((index) => build[`upgrade_${index}`]).length
    const crew = (build.sailors || 0) + (build.soldiers || 0) + (build.musketeers || 0) + (build.mercenaries || 0)
    return {
      id: build.id,
      name: build.build_name,
      ship: [build.ship?.name, build.ship?.rate ? `${t('common.rate')} ${build.ship.rate}` : '', build.ship?.ship_type].filter(Boolean).join(' · '),
      type: build.build_role_label || buildTypeLabels.value[build.build_type] || build.build_type || t('builds.types.balanced'),
      crew: t('builds.list.crew', { current: crew, max: stats.crew_capacity || build.ship?.crew_capacity || 0 }),
      upgrades: t('builds.list.upgradeSummary', { used: usedUpgrades, max: stats.upgrade_slots_available || 5 }),
      weapons: t('builds.list.weaponSummary', { count: stats.weapon_total || 0 }),
      specialists: t('builds.list.specialCrewSummary', { count: stats.special_crew_total || 0 }),
      upvotes: Number(build.upvote_count || 0),
      inventory: t('builds.list.inventorySummary', {
        ammo: stats.ammunition_slots_used ?? build.ammunition_slots?.length ?? 0,
        consumables: stats.consumable_slots_used ?? build.consumable_slots?.length ?? 0,
        hold: stats.hold_slots_used ?? build.hold_slots?.length ?? 0,
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
        listBuilds(search.value, buildType.value, classification.value),
        roles.value.length ? Promise.resolve(roles.value) : listBuildRoles(),
      ])
      builds.value = nextBuilds
      roles.value = nextRoles
    } catch (err) {
      error.value = err.message || t('builds.list.loadError')
    } finally {
      loading.value = false
    }
  }

  function resetDiscovery() {
    const hadFilters = hasFilters.value
    search.value = ''
    buildType.value = ''
    classification.value = ''
    showAll.value = true
    error.value = ''
    window.clearTimeout(searchTimer)
    if (!hadFilters) void loadBuilds()
  }

  function showAllBuilds() {
    resetDiscovery()
  }

  watch([search, buildType, classification], () => {
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
    searchTimer,
    discoveryGroups,
    hasFilters,
    hasActiveDiscovery,
    buildTypeOptions,
    buildTypeLabels,
    buildCountLabel,
    selectedDiscoveryLabel,
    resultLabels,
    buildRows,
    loadBuilds,
    resetDiscovery,
    showAllBuilds,
    localizedBuildDiscoveryGroups,
  }
}
