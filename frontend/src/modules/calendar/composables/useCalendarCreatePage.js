import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { dateInputValue, localDateFromInputs, timeInputValue } from '@/shared/datetime/localDateTime'
import {
  createFleetEvent,
  FLEET_EVENT_CATEGORIES,
  listRaidHelperOptions,
} from '@/modules/calendar/api/calendar'
import { useSession } from '@/modules/accounts/session'
import { listSquads } from '@/modules/squads/api/squads'

export function useCalendarCreatePage() {
  const route = useRoute()
  const router = useRouter()
  const { t } = useLocale()
  const { canManageFleet } = useSession()

  const now = new Date()
  now.setMinutes(0, 0, 0)
  const later = new Date(now)
  later.setHours(now.getHours() + 2)

  const squads = ref([])
  const loadingScopes = ref(false)
  const loadingRaidHelper = ref(false)
  const saving = ref(false)
  const error = ref('')
  const raidHelperError = ref('')
  const raidHelperOptions = ref([])
  const raidHelperSelections = reactive({})
  const form = reactive({
    title: '',
    category: 'training',
    scope: route.query.squad ? `squad:${route.query.squad}` : '',
    location: '',
    startDate: dateInputValue(now),
    startTime: timeInputValue(now),
    endDate: dateInputValue(later),
    endTime: timeInputValue(later),
    allDay: false,
    description: '',
    raidHelperEnabled: true,
  })

  const managedSquads = computed(() => squads.value.filter((squad) => squad.can_manage && squad.is_active))
  const scopeOptions = computed(() => {
    const options = []
    if (canManageFleet.value) options.push({ value: 'fleet', label: t('calendar.scopes.fleetWide') })
    options.push(...managedSquads.value.map((squad) => ({ value: `squad:${squad.id}`, label: squad.name })))
    return options
  })
  const canCreate = computed(() => scopeOptions.value.length > 0)
  const selectedSquadId = computed(() => (
    form.scope.startsWith('squad:') ? Number(form.scope.split(':')[1]) : null
  ))

  const categoryOptions = computed(() =>
    FLEET_EVENT_CATEGORIES.map((value) => ({ value, label: t(`calendar.categories.${value}`) })),
  )

  const startAt = computed(() => localDateFromInputs(form.startDate, form.allDay ? '00:00' : form.startTime))
  const endAt = computed(() => {
    const date = localDateFromInputs(form.endDate, form.allDay ? '00:00' : form.endTime)
    if (date && form.allDay) date.setDate(date.getDate() + 1)
    return date
  })
  const dateRangeInvalid = computed(() => !startAt.value || !endAt.value || endAt.value <= startAt.value)
  const selectedRaidHelperCount = computed(() => Object.values(raidHelperSelections).filter(Boolean).length)

  function clearRaidHelperSelections() {
    for (const key of Object.keys(raidHelperSelections)) delete raidHelperSelections[key]
  }

  function defaultTemplate(destination) {
    return destination.templates.find((template) => template.is_default) || destination.templates[0] || null
  }

  async function loadRaidHelperOptions() {
    raidHelperError.value = ''
    if (!form.raidHelperEnabled || !form.scope) {
      raidHelperOptions.value = []
      clearRaidHelperSelections()
      return
    }
    loadingRaidHelper.value = true
    try {
      const options = await listRaidHelperOptions({
        category: form.category,
        squadId: selectedSquadId.value ?? '',
      })
      const previous = { ...raidHelperSelections }
      clearRaidHelperSelections()
      raidHelperOptions.value = options
      for (const destination of options) {
        const allowedTemplateIds = new Set(destination.templates.map((template) => template.id))
        if (previous[destination.id] && allowedTemplateIds.has(Number(previous[destination.id]))) {
          raidHelperSelections[destination.id] = Number(previous[destination.id])
          continue
        }
        const template = defaultTemplate(destination)
        if (destination.is_default && template) raidHelperSelections[destination.id] = template.id
      }
    } catch (err) {
      raidHelperOptions.value = []
      clearRaidHelperSelections()
      raidHelperError.value = err.message || t('raidHelper.calendar.loadError')
    } finally {
      loadingRaidHelper.value = false
    }
  }

  function destinationSelected(destinationId) {
    return Boolean(raidHelperSelections[destinationId])
  }

  function toggleDestination(destination) {
    if (destinationSelected(destination.id)) {
      delete raidHelperSelections[destination.id]
      return
    }
    const template = defaultTemplate(destination)
    if (template) raidHelperSelections[destination.id] = template.id
  }

  function setDestinationTemplate(destinationId, value) {
    const templateId = Number(value)
    if (Number.isInteger(templateId) && templateId > 0) raidHelperSelections[destinationId] = templateId
  }

  async function loadScopes() {
    loadingScopes.value = true
    error.value = ''
    try {
      squads.value = await listSquads()
      const values = new Set(scopeOptions.value.map((option) => option.value))
      if (!values.has(form.scope)) form.scope = scopeOptions.value[0]?.value || ''
    } catch (err) {
      error.value = err.message || t('calendar.create.scopeLoadError')
    } finally {
      loadingScopes.value = false
    }
  }

  async function submitEvent() {
    error.value = ''
    if (dateRangeInvalid.value) {
      error.value = t('calendar.create.dateRangeInvalid')
      return
    }
    if (!form.scope) {
      error.value = t('calendar.create.noScopeError')
      return
    }

    saving.value = true
    try {
      const squadId = selectedSquadId.value
      await createFleetEvent({
        title: form.title,
        category: form.category,
        location: form.location || null,
        description: form.description || null,
        start_at: startAt.value.toISOString(),
        end_at: endAt.value.toISOString(),
        all_day: form.allDay,
        squad_id: squadId,
        raid_helper_enabled: form.raidHelperEnabled,
        raid_helper_dispatches: form.raidHelperEnabled
          ? Object.entries(raidHelperSelections)
            .filter(([, templateId]) => Boolean(templateId))
            .map(([destinationId, templateId]) => ({
              destination_id: Number(destinationId),
              template_id: Number(templateId),
            }))
          : [],
      })
      router.push(squadId ? { path: '/calendar', query: { squad: squadId } } : '/calendar')
    } catch (err) {
      error.value = err.message || t('calendar.create.saveError')
    } finally {
      saving.value = false
    }
  }

  watch(
    () => [form.category, form.scope, form.raidHelperEnabled],
    () => loadRaidHelperOptions(),
  )

  onMounted(async () => {
    await loadScopes()
    await loadRaidHelperOptions()
  })

  return {
    route,
    router,
    t,
    canManageFleet,
    now,
    later,
    squads,
    loadingScopes,
    loadingRaidHelper,
    saving,
    error,
    raidHelperError,
    raidHelperOptions,
    raidHelperSelections,
    form,
    managedSquads,
    scopeOptions,
    canCreate,
    selectedSquadId,
    categoryOptions,
    startAt,
    endAt,
    dateRangeInvalid,
    selectedRaidHelperCount,
    loadScopes,
    loadRaidHelperOptions,
    destinationSelected,
    toggleDestination,
    setDestinationTemplate,
    submitEvent,
    dateInputValue,
    localDateFromInputs,
    timeInputValue,
  }
}
