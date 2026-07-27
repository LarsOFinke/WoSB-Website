import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { dateInputValue, localDateFromInputs, timeInputValue } from '@/shared/datetime/localDateTime'
import { createFleetEvent, FLEET_EVENT_CATEGORIES } from '@/modules/calendar/api/calendar'
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
  const saving = ref(false)
  const error = ref('')
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
  })

  const managedSquads = computed(() => squads.value.filter((squad) => squad.can_manage && squad.is_active))
  const scopeOptions = computed(() => {
    const options = []
    if (canManageFleet.value) options.push({ value: 'fleet', label: t('calendar.scopes.fleetWide') })
    options.push(...managedSquads.value.map((squad) => ({ value: `squad:${squad.id}`, label: squad.name })))
    return options
  })
  const canCreate = computed(() => scopeOptions.value.length > 0)

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
      const squadId = form.scope.startsWith('squad:') ? Number(form.scope.split(':')[1]) : null
      await createFleetEvent({
        title: form.title,
        category: form.category,
        location: form.location || null,
        description: form.description || null,
        start_at: startAt.value.toISOString(),
        end_at: endAt.value.toISOString(),
        all_day: form.allDay,
        squad_id: squadId,
      })
      router.push(squadId ? { path: '/calendar', query: { squad: squadId } } : '/calendar')
    } catch (err) {
      error.value = err.message || t('calendar.create.saveError')
    } finally {
      saving.value = false
    }
  }

  onMounted(loadScopes)

  return {
    route,
    router,
    t,
    canManageFleet,
    now,
    later,
    squads,
    loadingScopes,
    saving,
    error,
    form,
    managedSquads,
    scopeOptions,
    canCreate,
    categoryOptions,
    startAt,
    endAt,
    dateRangeInvalid,
    loadScopes,
    submitEvent,
    dateInputValue,
    localDateFromInputs,
    timeInputValue,
  }
}
