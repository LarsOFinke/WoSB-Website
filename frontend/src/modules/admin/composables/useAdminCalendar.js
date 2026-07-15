import { computed, ref, watch } from 'vue'

import { deleteFleetEvent, FLEET_EVENT_CATEGORIES, listFleetEvents } from '@/modules/calendar/api/calendar'
import { calendarRequestRange, filterAndSortEvents, isoDate, shiftDate } from '@/modules/admin/domain/adminWorkspace'

export function useAdminCalendar({ isStaff, locale, t, clearConfirmation }) {
  const today = new Date()
  const defaultToDate = shiftDate(today, 90)

  const fleetEvents = ref([])
  const calendarCategory = ref('')
  const calendarSearch = ref('')
  const calendarFromDate = ref(isoDate(today))
  const calendarToDate = ref(isoDate(defaultToDate))
  const calendarLoading = ref(false)
  const calendarError = ref('')

  const filteredEvents = computed(() => filterAndSortEvents(fleetEvents.value, calendarSearch.value))
  const upcomingEvents = computed(() => filteredEvents.value.slice(0, 40))
  const nextOverviewEvent = computed(() => filteredEvents.value
    .find((event) => new Date(event.end_at || event.start_at) >= new Date()) || null)
  const eventCountLabel = computed(() => upcomingEvents.value.length === 1
    ? t('admin.calendar.summaryOne')
    : t('admin.calendar.summaryMany', { count: upcomingEvents.value.length }))
  const categoryOptions = computed(() => [
    { value: '', label: t('calendar.categories.all') },
    ...FLEET_EVENT_CATEGORIES.map((value) => ({ value, label: t(`calendar.categories.${value}`) })),
  ])

  function formatDateTime(value) {
    return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' })
      .format(new Date(value))
  }

  function formatEventRange(event) {
    if (event.all_day) {
      const date = new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(event.start_at))
      return `${date} · ${t('calendar.list.allDay')}`
    }
    const end = new Intl.DateTimeFormat(locale.value, { timeStyle: 'short' }).format(new Date(event.end_at))
    return `${formatDateTime(event.start_at)} – ${end}`
  }

  async function loadCalendar() {
    if (!isStaff.value) return
    calendarLoading.value = true
    calendarError.value = ''
    try {
      const range = calendarRequestRange(calendarFromDate.value, calendarToDate.value)
      fleetEvents.value = await listFleetEvents({ ...range, category: calendarCategory.value })
    } catch (err) {
      calendarError.value = err.message || t('admin.calendar.loadError')
    } finally {
      calendarLoading.value = false
    }
  }

  async function confirmDeleteEvent(eventId) {
    calendarError.value = ''
    try {
      await deleteFleetEvent(eventId)
      clearConfirmation()
      await loadCalendar()
    } catch (err) {
      calendarError.value = err.message || t('admin.calendar.deleteError')
    }
  }

  function resetCalendarFilters() {
    calendarCategory.value = ''
    calendarSearch.value = ''
    calendarFromDate.value = isoDate(today)
    calendarToDate.value = isoDate(defaultToDate)
  }

  watch([calendarCategory, calendarFromDate, calendarToDate], loadCalendar)

  return {
    fleetEvents, calendarCategory, calendarSearch, calendarFromDate, calendarToDate,
    calendarLoading, calendarError, filteredEvents, upcomingEvents, nextOverviewEvent, eventCountLabel,
    categoryOptions, formatDateTime, formatEventRange, loadCalendar, confirmDeleteEvent,
    resetCalendarFilters,
  }
}
