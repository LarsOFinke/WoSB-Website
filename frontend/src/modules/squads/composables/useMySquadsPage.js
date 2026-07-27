import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useLocale } from '@/locales'
import { listFleetEvents } from '@/modules/calendar/api/calendar'
import { listMySquads } from '@/modules/squads/api/squads'
import { upcomingEventsForSquads } from '@/modules/squads/mySquadsEvents'

export function useMySquadsPage() {
  const route = useRoute()
  const { locale, t } = useLocale()

  const squads = ref([])
  const events = ref([])
  const loading = ref(false)
  const error = ref('')

  const activeView = computed(() => route.query.view === 'events' ? 'events' : 'squads')
  const commandSquads = computed(() => squads.value.filter((squad) => squad.can_manage))
  const memberSquads = computed(() => squads.value.filter((squad) => !squad.can_manage))
  const upcomingSquadEvents = computed(() => upcomingEventsForSquads(events.value, squads.value))

  function eventsForSquad(squadId) {
    return upcomingSquadEvents.value.filter((event) => event.squad_id === squadId)
  }

  function nextEventForSquad(squadId) {
    return eventsForSquad(squadId)[0] || null
  }

  function formatEventDate(event) {
    if (!event) return t('mySquads.noUpcomingEvent')
    const start = new Date(event.start_at)
    if (event.all_day) {
      return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(start)
    }
    return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(start)
  }

  function roleLabel(squad) {
    return squad.current_user_role ? t(`squads.roles.${squad.current_user_role}`) : t('squads.roles.member')
  }

  function categoryLabel(event) {
    return t(`calendar.categories.${event.category || 'other'}`)
  }

  async function loadWorkspace() {
    loading.value = true
    error.value = ''
    try {
      const [mySquads, visibleEvents] = await Promise.all([
        listMySquads(),
        listFleetEvents({ start: new Date().toISOString() }),
      ])
      squads.value = mySquads
      events.value = visibleEvents
    } catch (err) {
      error.value = err.message || t('mySquads.loadError')
    } finally {
      loading.value = false
    }
  }

  onMounted(loadWorkspace)

  return {
    route,
    locale,
    t,
    squads,
    events,
    loading,
    error,
    activeView,
    commandSquads,
    memberSquads,
    upcomingSquadEvents,
    eventsForSquad,
    nextEventForSquad,
    formatEventDate,
    roleLabel,
    categoryLabel,
    loadWorkspace,
    upcomingEventsForSquads,
  }
}
