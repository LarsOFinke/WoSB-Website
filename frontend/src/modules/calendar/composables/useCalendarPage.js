import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useLocale } from '@/locales'
import { deleteFleetEvent, FLEET_EVENT_CATEGORIES, listFleetEvents } from '@/modules/calendar/api/calendar'
import {
  calendarDayClasses,
  dateKey,
  daysInRange,
  eventsOnDate,
  filtersForScope,
  isSameDay,
  monthGridRange,
  newEventTargetForScope,
} from '@/modules/calendar/domain/calendarGrid'
import { useSession } from '@/modules/accounts/session'
import { listSquads } from '@/modules/squads/api/squads'

export function useCalendarPage() {
  const route = useRoute()
  const { locale, t } = useLocale()
  const { canManageFleet } = useSession()
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const activeMonth = ref(new Date(today.getFullYear(), today.getMonth(), 1))
  const selectedDate = ref(new Date(today))
  const category = ref('')
  const scope = ref(route.query.squad ? `squad:${route.query.squad}` : 'all')
  const events = ref([])
  const squads = ref([])
  const loading = ref(false)
  const error = ref('')
  const cancellingId = ref(null)

  const weekdayLabels = computed(() => {
    const monday = new Date(2024, 0, 1)
    return Array.from({ length: 7 }, (_, index) =>
      new Intl.DateTimeFormat(locale.value, { weekday: 'short' }).format(new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + index)),
    )
  })
  const monthLabel = computed(() => new Intl.DateTimeFormat(locale.value, { month: 'long', year: 'numeric' }).format(activeMonth.value))
  const monthRange = computed(() => monthGridRange(activeMonth.value))
  const calendarDays = computed(() => daysInRange(monthRange.value))
  const visibleSquads = computed(() => squads.value.filter((squad) => squad.is_member || squad.can_manage))
  const managedSquads = computed(() => squads.value.filter((squad) => squad.can_manage && squad.is_active))
  const canCreateEvent = computed(() => canManageFleet.value || managedSquads.value.length > 0)
  const categoryOptions = computed(() => [
    { value: '', label: t('calendar.categories.all') },
    ...FLEET_EVENT_CATEGORIES.map((value) => ({ value, label: t(`calendar.categories.${value}`) })),
  ])
  const scopeOptions = computed(() => [
    { value: 'all', label: t('calendar.scopes.allVisible') },
    { value: 'fleet', label: t('calendar.scopes.fleetWide') },
    ...visibleSquads.value.map((squad) => ({ value: `squad:${squad.id}`, label: squad.name })),
  ])
  const eventCountLabel = computed(() => events.value.length === 1
    ? t('calendar.list.summaryOne')
    : t('calendar.list.summaryMany', { count: events.value.length }))
  const selectedEvents = computed(() => eventsForDate(selectedDate.value))
  const newEventTarget = computed(() => newEventTargetForScope(scope.value))

  function eventsForDate(date) {
    return eventsOnDate(events.value, date)
  }

  function dayClasses(date) {
    return calendarDayClasses({
      date,
      activeMonth: activeMonth.value,
      today,
      selectedDate: selectedDate.value,
      events: events.value,
    })
  }

  function dayLabel(date) {
    return new Intl.DateTimeFormat(locale.value, { day: 'numeric' }).format(date)
  }

  function fullDateLabel(date) {
    return new Intl.DateTimeFormat(locale.value, { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(date)
  }

  function formatEventTime(event) {
    if (event.all_day) return t('calendar.list.allDay')
    const formatter = new Intl.DateTimeFormat(locale.value, { hour: '2-digit', minute: '2-digit' })
    return `${formatter.format(new Date(event.start_at))}–${formatter.format(new Date(event.end_at))}`
  }

  function eventScopeLabel(event) {
    return event.squad?.name || t('calendar.scopes.fleetWide')
  }

  function selectDay(date) {
    selectedDate.value = new Date(date)
  }

  function moveMonth(offset) {
    activeMonth.value = new Date(activeMonth.value.getFullYear(), activeMonth.value.getMonth() + offset, 1)
  }

  function jumpToToday() {
    activeMonth.value = new Date(today.getFullYear(), today.getMonth(), 1)
    selectedDate.value = new Date(today)
  }

  function scopeFilters() {
    return filtersForScope(scope.value)
  }

  async function loadEvents() {
    loading.value = true
    error.value = ''
    try {
      events.value = await listFleetEvents({
        start: monthRange.value.gridStart.toISOString(),
        end: monthRange.value.gridEnd.toISOString(),
        category: category.value,
        ...scopeFilters(),
      })
    } catch (err) {
      error.value = err.message || t('calendar.list.loadError')
    } finally {
      loading.value = false
    }
  }

  async function loadSquadScopes() {
    try {
      squads.value = await listSquads()
      const allowedValues = new Set(scopeOptions.value.map((option) => option.value))
      if (!allowedValues.has(scope.value)) scope.value = 'all'
    } catch {
      squads.value = []
      scope.value = 'all'
    }
  }

  async function cancelEvent(event) {
    if (!window.confirm(t('calendar.list.cancelConfirm', { title: event.title }))) return
    cancellingId.value = event.id
    error.value = ''
    try {
      await deleteFleetEvent(event.id)
      await loadEvents()
    } catch (err) {
      error.value = err.message || t('calendar.list.cancelError')
    } finally {
      cancellingId.value = null
    }
  }

  watch([activeMonth, category, scope], loadEvents)
  onMounted(async () => {
    await loadSquadScopes()
    await loadEvents()
  })

  return {
    route, locale, t, canManageFleet, today, activeMonth, selectedDate, category,
    scope, events, squads, loading, error, cancellingId, weekdayLabels, monthLabel,
    monthRange, calendarDays, visibleSquads, managedSquads, canCreateEvent,
    categoryOptions, scopeOptions, eventCountLabel, selectedEvents, newEventTarget,
    dateKey, isSameDay, eventsForDate, dayClasses, dayLabel, fullDateLabel,
    formatEventTime, eventScopeLabel, selectDay, moveMonth, jumpToToday,
    scopeFilters, loadEvents, loadSquadScopes, cancelEvent,
  }
}
