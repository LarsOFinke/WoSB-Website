<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { useLocale } from '@/locales'
import { deleteFleetEvent, FLEET_EVENT_CATEGORIES, listFleetEvents } from '@/modules/calendar/api/calendar'
import { useSession } from '@/modules/accounts/session'
import { listSquads } from '@/modules/squads/api/squads'

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

const monthLabel = computed(() =>
  new Intl.DateTimeFormat(locale.value, { month: 'long', year: 'numeric' }).format(activeMonth.value),
)

const monthRange = computed(() => {
  const year = activeMonth.value.getFullYear()
  const month = activeMonth.value.getMonth()
  const firstOfMonth = new Date(year, month, 1)
  const lastOfMonth = new Date(year, month + 1, 0)
  const gridStart = new Date(firstOfMonth)
  gridStart.setDate(firstOfMonth.getDate() - ((firstOfMonth.getDay() + 6) % 7))
  const gridEnd = new Date(lastOfMonth)
  gridEnd.setDate(lastOfMonth.getDate() + (6 - ((lastOfMonth.getDay() + 6) % 7)))
  gridEnd.setHours(23, 59, 59, 999)
  return { gridStart, gridEnd }
})

const calendarDays = computed(() => {
  const days = []
  const cursor = new Date(monthRange.value.gridStart)
  while (cursor <= monthRange.value.gridEnd) {
    days.push(new Date(cursor))
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
})

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

const eventCountLabel = computed(() =>
  events.value.length === 1 ? t('calendar.list.summaryOne') : t('calendar.list.summaryMany', { count: events.value.length }),
)

const selectedEvents = computed(() => eventsForDate(selectedDate.value))
const newEventTarget = computed(() => {
  if (scope.value.startsWith('squad:')) {
    return { path: '/calendar/new', query: { squad: scope.value.split(':')[1] } }
  }
  return '/calendar/new'
})

function dateKey(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-')
}

function isSameDay(left, right) {
  return dateKey(left) === dateKey(right)
}

function eventsForDate(date) {
  const key = dateKey(date)
  return events.value.filter((event) => {
    const start = new Date(event.start_at)
    const end = new Date(new Date(event.end_at).getTime() - 1)
    const cursor = new Date(start)
    cursor.setHours(0, 0, 0, 0)
    const endDay = new Date(end)
    endDay.setHours(0, 0, 0, 0)
    while (cursor <= endDay) {
      if (dateKey(cursor) === key) return true
      cursor.setDate(cursor.getDate() + 1)
    }
    return false
  })
}

function dayClasses(date) {
  return {
    'is-outside-month': date.getMonth() !== activeMonth.value.getMonth(),
    'is-today': isSameDay(date, today),
    'is-selected': isSameDay(date, selectedDate.value),
    'has-events': eventsForDate(date).length > 0,
  }
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
  if (scope.value === 'fleet') return { fleetOnly: true, squadId: '' }
  if (scope.value.startsWith('squad:')) return { fleetOnly: false, squadId: scope.value.split(':')[1] }
  return { fleetOnly: false, squadId: '' }
}

async function loadEvents() {
  loading.value = true
  error.value = ''
  try {
    const filters = scopeFilters()
    events.value = await listFleetEvents({
      start: monthRange.value.gridStart.toISOString(),
      end: monthRange.value.gridEnd.toISOString(),
      category: category.value,
      ...filters,
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
</script>

<template>
  <section class="calendar-page" aria-labelledby="calendar-title">
    <div class="wire-frame page-frame compact-frame calendar-frame">
      <header class="wire-section build-list-hero calendar-hero">
        <div>
          <p class="eyebrow">{{ t('calendar.list.eyebrow') }}</p>
          <h1 id="calendar-title">{{ t('calendar.list.title') }}</h1>
          <p>{{ t('calendar.list.subtitle') }}</p>
        </div>
        <div class="hero-actions">
          <span class="summary-pill">{{ eventCountLabel }}</span>
          <RouterLink v-if="canCreateEvent" class="button-box primary-action" :to="newEventTarget">
            {{ t('calendar.list.newEvent') }}
          </RouterLink>
        </div>
      </header>

      <section class="wire-section build-filter-panel calendar-filter-panel" :aria-label="t('calendar.list.filtersLabel')">
        <div>
          <h2>{{ t('calendar.list.filtersTitle') }}</h2>
          <p>{{ t('calendar.list.filtersText') }}</p>
        </div>
        <div class="calendar-toolbar">
          <div class="calendar-navigation" :aria-label="t('calendar.list.monthNavigation')">
            <button class="button-box calendar-nav-button" type="button" @click="moveMonth(-1)">‹</button>
            <button class="button-box" type="button" @click="jumpToToday">{{ t('calendar.list.today') }}</button>
            <button class="button-box calendar-nav-button" type="button" @click="moveMonth(1)">›</button>
          </div>
          <label class="filter-box type-filter-box select-shell toolbar-select-shell calendar-category-filter">
            <select v-model="scope" :aria-label="t('calendar.fields.scope')">
              <option v-for="option in scopeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
          <label class="filter-box type-filter-box select-shell toolbar-select-shell calendar-category-filter">
            <select v-model="category" :aria-label="t('calendar.fields.category')">
              <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
      </section>

      <section class="calendar-layout">
        <div class="wire-section calendar-month-panel" aria-live="polite">
          <div class="calendar-month-heading">
            <div>
              <p class="eyebrow">{{ t('calendar.list.month') }}</p>
              <h2>{{ monthLabel }}</h2>
            </div>
            <p class="muted">{{ t('calendar.list.windowsHint') }}</p>
          </div>

          <p v-if="loading" class="muted table-state">{{ t('calendar.list.loading') }}</p>
          <p v-else-if="error" class="error-text table-state">{{ error }}</p>

          <div class="fleet-calendar-grid" :aria-label="monthLabel">
            <span v-for="weekday in weekdayLabels" :key="weekday" class="calendar-weekday">{{ weekday }}</span>
            <button
              v-for="day in calendarDays"
              :key="dateKey(day)"
              class="calendar-day"
              :class="dayClasses(day)"
              type="button"
              @click="selectDay(day)"
            >
              <span class="calendar-day-number">{{ dayLabel(day) }}</span>
              <span class="calendar-day-events">
                <span
                  v-for="event in eventsForDate(day).slice(0, 3)"
                  :key="event.id"
                  class="calendar-event-chip"
                  :class="`event-${event.category}`"
                >
                  {{ event.squad ? `${event.squad.name} · ` : '' }}{{ formatEventTime(event) }} · {{ event.title }}
                </span>
                <span v-if="eventsForDate(day).length > 3" class="calendar-more-chip">
                  {{ t('calendar.list.moreEvents', { count: eventsForDate(day).length - 3 }) }}
                </span>
              </span>
            </button>
          </div>
        </div>

        <aside class="wire-section calendar-agenda-panel" :aria-label="t('calendar.list.selectedDay')">
          <div class="section-heading-row">
            <div>
              <p class="eyebrow">{{ t('calendar.list.selectedDay') }}</p>
              <h2>{{ fullDateLabel(selectedDate) }}</h2>
            </div>
          </div>

          <p v-if="selectedEvents.length === 0" class="muted table-state">{{ t('calendar.list.noEventsForDay') }}</p>
          <div v-else class="calendar-agenda-list">
            <article v-for="event in selectedEvents" :key="event.id" class="calendar-agenda-card">
              <div class="calendar-agenda-topline">
                <span class="type-pill" :class="`event-${event.category}`">{{ t(`calendar.categories.${event.category}`) }}</span>
                <span>{{ formatEventTime(event) }}</span>
              </div>
              <span class="calendar-scope-badge">{{ eventScopeLabel(event) }}</span>
              <h3>{{ event.title }}</h3>
              <p v-if="event.location" class="muted">{{ event.location }}</p>
              <p v-if="event.description" class="preserve-lines">{{ event.description }}</p>
              <p class="muted">{{ t('calendar.list.createdBy', { name: event.owner.display_name }) }}</p>
              <button
                v-if="event.can_manage"
                class="danger-action calendar-cancel-action"
                type="button"
                :disabled="cancellingId === event.id"
                @click="cancelEvent(event)"
              >
                {{ cancellingId === event.id ? t('calendar.list.cancelling') : t('calendar.list.cancelEvent') }}
              </button>
            </article>
          </div>
        </aside>
      </section>
    </div>
  </section>
</template>
