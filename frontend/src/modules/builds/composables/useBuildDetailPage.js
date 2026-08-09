import { computed, onMounted, ref } from 'vue'
import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'
import { buildCategoryVisuals, buildCrewVisuals, buildOptionVisual } from '@/modules/builds/buildVisuals'
import { absoluteFileUrl } from '@/modules/files/api/files'
import { useLocale } from '@/locales'
import { addBuildUpvote, getBuild, getBuildOptions, removeBuildUpvote } from '@/modules/builds/api/builds'
import { useBuildPrintActions } from '@/modules/builds/composables/useBuildPrintActions'
import {
  activeBuildEffects,
  buildUpgrades,
  commandDeckSlots,
  crewDistribution,
  formatBuildModifier,
  inventoryCategory,
  roundByPrecision,
  shareLinkMeta,
  slotItem,
  slotLabel as buildSlotLabel,
  slotQuantity,
  specialistLabel as buildSpecialistLabel,
  translatedStatRows,
  weaponArcRows as createWeaponArcRows,
} from '@/modules/builds/domain/buildDetailPresentation'
import { copyBuildShareLink } from '@/modules/builds/shareBuild'
import { localizedBuildDiscoveryGroups } from '@/modules/builds/domain/buildDiscovery'
import { GINGER_SPECIALIST_NAME } from '@/modules/builds/domain/specialistSelection'
import { useSession } from '@/modules/accounts/session'

export function useBuildDetailPage(props) {
  const { optionLabel, t } = useLocale()
  const { user, isStaff } = useSession()
  const build = ref(null)
  const optionCatalog = ref({ categories: [], options: {}, stat_definitions: [], research_upgrade_slot_effects: {}, research_upgrade_slot_grant: 0, limits: {} })
  const loading = ref(false)
  const error = ref('')
  const shareStatus = ref('')
  const voteBusy = ref(false)
  const voteError = ref('')
  const categoryFallbackImages = buildCategoryVisuals
  const crewFallbackImages = buildCrewVisuals
  const canEdit = computed(() => Number(build.value?.owner_id) === Number(user.value?.id) && !build.value?.is_official_template)
  const canCachePrintout = computed(() => canEdit.value || isStaff.value)
  const printActions = useBuildPrintActions(build, { t, optionLabel, optionImage, canCache: canCachePrintout })

  const weaponArcRows = computed(() => createWeaponArcRows(build.value, t))
  const crewTotal = computed(() => build.value?.ship_stats?.crew_total || 0)
  const upgrades = computed(() => buildUpgrades(build.value))
  const commandDeckUpgradeSlots = computed(() => commandDeckSlots(build.value, optionLabel))
  const specialCrewSlots = computed(() => build.value?.special_crew_slots || [])
  const regularSpecialCrewSlots = computed(() => specialCrewSlots.value.filter((slot) => slotItem(slot) !== GINGER_SPECIALIST_NAME))
  const gingerSpecialCrewSlot = computed(() => specialCrewSlots.value.find((slot) => slotItem(slot) === GINGER_SPECIALIST_NAME) || null)
  const classificationLabels = computed(() => {
    const labelByValue = new Map(
      localizedBuildDiscoveryGroups(t).flatMap((group) => group.items.map((item) => [item.value, item.label])),
    )
    return (build.value?.classification_tags || []).map((value) => ({ value, label: labelByValue.get(value) || value }))
  })
  const ammunitionSlots = computed(() => build.value?.ammunition_slots || [])
  const consumableSlots = computed(() => build.value?.consumable_slots || [])
  const holdSlots = computed(() => build.value?.hold_slots || [])
  const crewDistributionRows = computed(() => crewDistribution(build.value, t, crewFallbackImages, slotPlaceholderSrc))
  const statRows = computed(() => translatedStatRows(build.value, t))
  const activeEffectRows = computed(() => activeBuildEffects(statRows.value))

  function optionMeta(categoryKey, name) {
    return (optionCatalog.value.options?.[categoryKey] || []).find((option) => option.name === name)
  }

  function optionImage(categoryKey, name) {
    if (!name) return categoryFallbackImages[categoryKey] || slotPlaceholderSrc
    return buildOptionVisual(absoluteFileUrl(optionMeta(categoryKey, name)?.image_url), categoryKey, categoryFallbackImages[categoryKey])
      || slotPlaceholderSrc
  }

  function slotLabel(slot) {
    return buildSlotLabel(slot, optionLabel)
  }

  function inventoryImage(fieldName, slot) {
    return optionImage(inventoryCategory(fieldName), slotItem(slot))
  }

  function specialistLabel(slot) {
    return buildSpecialistLabel(slot, optionLabel)
  }

  async function shareBuild() {
    shareStatus.value = ''
    try {
      await copyBuildShareLink(build.value.id)
      shareStatus.value = t('builds.share.copied')
    } catch {
      shareStatus.value = t('builds.share.error')
    }
  }

  function buildTypeLabel(value) {
    if (build.value?.build_role_label) return build.value.build_role_label
    const translated = t(`builds.types.${value || 'balanced'}`)
    return translated.startsWith('builds.types.') ? (value || 'Balanced') : translated
  }

  async function toggleUpvote() {
    if (!build.value || voteBusy.value) return
    voteBusy.value = true
    voteError.value = ''
    try {
      const state = build.value.has_upvoted
        ? await removeBuildUpvote(build.value.id)
        : await addBuildUpvote(build.value.id)
      build.value.upvote_count = state.upvote_count
      build.value.has_upvoted = state.has_upvoted
    } catch (err) {
      voteError.value = err.message || t('builds.voting.error')
    } finally {
      voteBusy.value = false
    }
  }

  function formatModifier(row) {
    return formatBuildModifier(row)
  }

  async function loadBuild() {
    loading.value = true
    error.value = ''
    try {
      build.value = await getBuild(props.id)
      optionCatalog.value = await getBuildOptions(build.value?.ship?.id || build.value?.ship_id || null)
    } catch (err) {
      error.value = err.message || t('builds.detail.loadError')
    } finally {
      loading.value = false
    }
  }

  onMounted(loadBuild)

  return {
    optionLabel, t, user, build, optionCatalog, loading, error, shareStatus, voteBusy, voteError,
    ...printActions,
    categoryFallbackImages, crewFallbackImages, weaponArcRows, crewTotal, canEdit,
    upgrades, commandDeckUpgradeSlots, specialCrewSlots, regularSpecialCrewSlots,
    gingerSpecialCrewSlot, classificationLabels, ammunitionSlots,
    consumableSlots, holdSlots, crewDistributionRows, optionMeta, optionImage,
    inventoryCategory, slotItem, slotLabel, slotQuantity, inventoryImage,
    specialistLabel, shareLinkMeta, shareBuild, buildTypeLabel, toggleUpvote, roundByPrecision,
    formatModifier, statRows, activeEffectRows, loadBuild,
  }
}
