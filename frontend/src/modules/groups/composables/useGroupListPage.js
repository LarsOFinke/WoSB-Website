import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { listGroups } from '@/modules/groups/api/groups'
import { useSession } from '@/modules/accounts/session'

export function useGroupListPage() {
  const { t } = useLocale()
  const { canAuthorContent } = useSession()

  const groups = ref([])
  const search = ref('')
  const focus = ref('')
  const maxShipRate = ref('')
  const minShipRate = ref('')
  const loading = ref(false)
  const error = ref('')
  let searchTimer = null

  const rateOptions = [7, 6, 5, 4, 3, 2, 1]

  const focusOptions = computed(() => [
    { value: '', label: t('groups.focus.all') },
    { value: 'pve_farming', label: t('focus.pve_farming') },
    { value: 'pve_imp_hunting', label: t('focus.pve_imp_hunting') },
    { value: 'pve_general', label: t('focus.pve_general') },
    { value: 'pvp_open_world', label: t('focus.pvp_open_world') },
    { value: 'pvp_arena', label: t('focus.pvp_arena') },
    { value: 'pvp_general', label: t('focus.pvp_general') },
    { value: 'trading', label: t('focus.trading') },
    { value: 'other', label: t('focus.other') },
  ])

  const groupCountLabel = computed(() =>
    groups.value.length === 1 ? t('groups.list.summaryOne') : t('groups.list.summaryMany', { count: groups.value.length }),
  )

  const rateRangeInvalid = computed(() =>
    minShipRate.value && maxShipRate.value && Number(maxShipRate.value) > Number(minShipRate.value),
  )

  function rateRequirement(group) {
    if (group.min_ship_rate && group.max_ship_rate) {
      return t('groups.list.rateRange', { max: group.max_ship_rate, min: group.min_ship_rate })
    }
    if (group.min_ship_rate) return t('groups.list.minRate', { value: group.min_ship_rate })
    if (group.max_ship_rate) return t('groups.list.maxRate', { value: group.max_ship_rate })
    return t('groups.detail.anyRate')
  }

  function formatSchedule(group) {
    if (!group.scheduled_start_at) return t('groups.detail.noSchedule')
    const start = new Date(group.scheduled_start_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    if (!group.scheduled_end_at) return start
    const end = new Date(group.scheduled_end_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    return `${start} – ${end}`
  }

  function groupMeta(group) {
    const parts = [t(`focus.${group.focus}`)]
    if (group.scheduled_start_at) parts.push(formatSchedule(group))
    if (group.min_ship_rate || group.max_ship_rate) parts.push(rateRequirement(group))
    return parts.join(' · ')
  }

  async function loadGroups() {
    if (rateRangeInvalid.value) {
      groups.value = []
      error.value = t('groups.list.rateFilterInvalid')
      return
    }

    loading.value = true
    error.value = ''
    try {
      groups.value = await listGroups({
        search: search.value,
        focus: focus.value,
        minShipRate: minShipRate.value,
        maxShipRate: maxShipRate.value,
      })
    } catch (err) {
      error.value = err.message || t('groups.list.loadError')
    } finally {
      loading.value = false
    }
  }

  watch([search, focus, minShipRate, maxShipRate], () => {
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
    focus,
    maxShipRate,
    minShipRate,
    loading,
    error,
    searchTimer,
    rateOptions,
    focusOptions,
    groupCountLabel,
    rateRangeInvalid,
    rateRequirement,
    formatSchedule,
    groupMeta,
    loadGroups,
  }
}
