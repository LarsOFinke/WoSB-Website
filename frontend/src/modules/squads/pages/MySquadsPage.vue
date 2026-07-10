<script setup>
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { listFleetEvents } from '@/modules/calendar/api/calendar'
import { listMySquads } from '@/modules/squads/api/squads'

const { locale, t } = useLocale()

const squads = ref([])
const events = ref([])
const loading = ref(false)
const error = ref('')

const commandSquads = computed(() => squads.value.filter((squad) => squad.can_manage))
const memberSquads = computed(() => squads.value.filter((squad) => !squad.can_manage))
const upcomingSquadEvents = computed(() => {
  const squadIds = new Set(squads.value.map((squad) => squad.id))
  return events.value
    .filter((event) => event.squad_id && squadIds.has(event.squad_id))
    .sort((left, right) => new Date(left.start_at) - new Date(right.start_at))
})

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
</script>

<template>
  <section class="my-squads-page" aria-labelledby="my-squads-title">
    <div class="wire-frame page-frame compact-frame my-squads-frame">
      <PageHeader
        :eyebrow="t('mySquads.eyebrow')"
        :title="t('mySquads.title')"
        :description="t('mySquads.subtitle')"
        title-id="my-squads-title"
      >
        <template #actions>
          <RouterLink class="button-box" to="/squads">{{ t('mySquads.allSquads') }}</RouterLink>
          <RouterLink class="button-box primary-action" to="/calendar">{{ t('mySquads.openCalendar') }}</RouterLink>
        </template>
      </PageHeader>

      <p v-if="loading" class="wire-section muted table-state">{{ t('mySquads.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text table-state">{{ error }}</p>

      <template v-else>
        <section class="workspace-metric-grid my-squads-metrics" :aria-label="t('mySquads.title')">
          <MetricCard :label="t('mySquads.metrics.assignments')" :value="squads.length" :hint="t('mySquads.metrics.assignmentsHint')" />
          <MetricCard :label="t('mySquads.metrics.command')" :value="commandSquads.length" :hint="t('mySquads.metrics.commandHint')" tone="accent" />
          <MetricCard :label="t('mySquads.metrics.events')" :value="upcomingSquadEvents.length" :hint="t('mySquads.metrics.eventsHint')" />
        </section>

        <section v-if="squads.length === 0" class="wire-section empty-state my-squads-empty">
          <span class="squad-mark"><AppIcon name="users" :size="24" /></span>
          <h2>{{ t('mySquads.emptyTitle') }}</h2>
          <p>{{ t('mySquads.emptyText') }}</p>
          <RouterLink class="button-box" to="/squads">{{ t('mySquads.browseSquads') }}</RouterLink>
        </section>

        <template v-else>
          <section v-if="commandSquads.length" class="my-squads-section" aria-labelledby="my-command-squads-title">
            <div class="workspace-section-heading my-squads-section-heading">
              <div>
                <p class="eyebrow">{{ t('mySquads.commandEyebrow') }}</p>
                <h2 id="my-command-squads-title">{{ t('mySquads.commandTitle') }}</h2>
                <p>{{ t('mySquads.commandText') }}</p>
              </div>
              <span class="summary-pill">{{ commandSquads.length }}</span>
            </div>

            <div class="my-squads-grid">
              <article v-for="squad in commandSquads" :key="squad.id" class="wire-section my-squad-card is-command">
                <div class="my-squad-card-heading">
                  <span class="squad-mark"><AppIcon name="shield" :size="21" /></span>
                  <div>
                    <p class="eyebrow">{{ roleLabel(squad) }}</p>
                    <h3>{{ squad.name }}</h3>
                  </div>
                  <span class="type-pill event-training">{{ t('mySquads.commandBadge') }}</span>
                </div>

                <p>{{ squad.description || t('squads.list.noDescription') }}</p>

                <dl class="my-squad-facts">
                  <div><dt>{{ t('squads.fields.focus') }}</dt><dd>{{ squad.focus || t('squads.list.noFocus') }}</dd></div>
                  <div><dt>{{ t('squads.fields.members') }}</dt><dd>{{ squad.max_members ? `${squad.member_count}/${squad.max_members}` : squad.member_count }}</dd></div>
                  <div><dt>{{ t('mySquads.nextEvent') }}</dt><dd>{{ nextEventForSquad(squad.id)?.title || t('mySquads.noUpcomingEvent') }}</dd></div>
                </dl>
                <p v-if="nextEventForSquad(squad.id)" class="my-squad-next-date">{{ formatEventDate(nextEventForSquad(squad.id)) }}</p>

                <div class="my-squad-actions">
                  <RouterLink class="small-action" :to="`/squads/${squad.id}`">{{ t('mySquads.manageSquad') }}</RouterLink>
                  <RouterLink class="small-action" :to="{ path: '/calendar', query: { squad: squad.id } }">{{ t('mySquads.squadCalendar') }}</RouterLink>
                  <RouterLink class="small-action primary-action" :to="{ path: '/calendar/new', query: { squad: squad.id } }">{{ t('mySquads.planEvent') }}</RouterLink>
                </div>
              </article>
            </div>
          </section>

          <section v-if="memberSquads.length" class="my-squads-section" aria-labelledby="my-member-squads-title">
            <div class="workspace-section-heading my-squads-section-heading">
              <div>
                <p class="eyebrow">{{ t('mySquads.memberEyebrow') }}</p>
                <h2 id="my-member-squads-title">{{ t('mySquads.memberTitle') }}</h2>
                <p>{{ t('mySquads.memberText') }}</p>
              </div>
              <span class="summary-pill">{{ memberSquads.length }}</span>
            </div>

            <div class="my-squads-grid">
              <article v-for="squad in memberSquads" :key="squad.id" class="wire-section my-squad-card">
                <div class="my-squad-card-heading">
                  <span class="squad-mark"><AppIcon name="users" :size="21" /></span>
                  <div>
                    <p class="eyebrow">{{ roleLabel(squad) }}</p>
                    <h3>{{ squad.name }}</h3>
                  </div>
                </div>

                <p>{{ squad.description || t('squads.list.noDescription') }}</p>

                <dl class="my-squad-facts">
                  <div><dt>{{ t('squads.fields.leader') }}</dt><dd>{{ squad.leader?.display_name || t('squads.list.noLeader') }}</dd></div>
                  <div><dt>{{ t('squads.fields.members') }}</dt><dd>{{ squad.max_members ? `${squad.member_count}/${squad.max_members}` : squad.member_count }}</dd></div>
                  <div><dt>{{ t('mySquads.nextEvent') }}</dt><dd>{{ nextEventForSquad(squad.id)?.title || t('mySquads.noUpcomingEvent') }}</dd></div>
                </dl>
                <p v-if="nextEventForSquad(squad.id)" class="my-squad-next-date">{{ formatEventDate(nextEventForSquad(squad.id)) }}</p>

                <div class="my-squad-actions">
                  <RouterLink class="small-action" :to="`/squads/${squad.id}`">{{ t('mySquads.openSquad') }}</RouterLink>
                  <RouterLink class="small-action" :to="{ path: '/calendar', query: { squad: squad.id } }">{{ t('mySquads.squadCalendar') }}</RouterLink>
                </div>
              </article>
            </div>
          </section>

          <section v-if="upcomingSquadEvents.length" class="wire-section my-squads-agenda" aria-labelledby="my-squads-agenda-title">
            <div class="workspace-section-heading compact-heading">
              <div>
                <p class="eyebrow">{{ t('mySquads.agendaEyebrow') }}</p>
                <h2 id="my-squads-agenda-title">{{ t('mySquads.agendaTitle') }}</h2>
                <p>{{ t('mySquads.agendaText') }}</p>
              </div>
            </div>
            <div class="my-squads-agenda-list">
              <RouterLink
                v-for="event in upcomingSquadEvents.slice(0, 6)"
                :key="event.id"
                class="my-squads-agenda-row"
                :to="{ path: '/calendar', query: { squad: event.squad_id } }"
              >
                <span class="calendar-event-dot" :class="`event-${event.category}`"></span>
                <span><strong>{{ event.title }}</strong><small>{{ event.squad?.name }} · {{ formatEventDate(event) }}</small></span>
                <b>→</b>
              </RouterLink>
            </div>
          </section>
        </template>
      </template>
    </div>
  </section>
</template>
