<script setup>
import { useCalendarPage } from '@/modules/calendar/composables/useCalendarPage.js'

const {
  route, locale, t, canManageFleet, today,
  activeMonth, selectedDate, category, scope, events,
  squads, loading, error, cancellingId, retryingId, linkedEventId, weekdayLabels,
  monthLabel, monthRange, calendarDays, visibleSquads, managedSquads,
  canCreateEvent, categoryOptions, scopeOptions, eventCountLabel, selectedEvents,
  newEventTarget, dateKey, isSameDay, eventsForDate, dayClasses,
  dayLabel, fullDateLabel, formatEventTime, eventScopeLabel, selectDay,
  moveMonth, jumpToToday, scopeFilters, loadEvents, loadSquadScopes,
  retryRaidHelper, cancelEvent,
} = useCalendarPage()
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
            <article
              v-for="event in selectedEvents"
              :id="`calendar-event-${event.id}`"
              :key="event.id"
              class="calendar-agenda-card"
              :class="{ 'is-linked-event': event.id === linkedEventId }"
            >
              <div class="calendar-agenda-topline">
                <span class="type-pill" :class="`event-${event.category}`">{{ t(`calendar.categories.${event.category}`) }}</span>
                <span>{{ formatEventTime(event) }}</span>
              </div>
              <span class="calendar-scope-badge">{{ eventScopeLabel(event) }}</span>
              <h3>{{ event.title }}</h3>
              <p v-if="event.location" class="muted">{{ event.location }}</p>
              <p v-if="event.description" class="preserve-lines">{{ event.description }}</p>
              <p class="muted">{{ t('calendar.list.createdBy', { name: event.owner.display_name }) }}</p>
              <div v-if="event.can_manage && event.raid_helper_links?.length" class="raid-helper-sync-list">
                <p class="field-label">{{ t('raidHelper.calendar.syncStatus') }}</p>
                <div v-for="link in event.raid_helper_links" :key="link.id" class="raid-helper-sync-row">
                  <span><strong>{{ link.destination_name }}</strong> · {{ link.template_name }}</span>
                  <span class="type-pill" :class="`raid-helper-status-${link.status}`">{{ t(`raidHelper.calendar.status.${link.status}`) }}</span>
                  <small v-if="link.error_message" class="error-text">{{ link.error_message }}</small>
                </div>
              </div>
              <button
                v-if="event.can_manage && event.raid_helper_links?.some((link) => link.status === 'failed')"
                class="small-action"
                type="button"
                :disabled="retryingId === event.id"
                @click="retryRaidHelper(event)"
              >
                {{ retryingId === event.id ? t('raidHelper.calendar.retrying') : t('raidHelper.calendar.retry') }}
              </button>
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
