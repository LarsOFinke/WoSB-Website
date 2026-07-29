<script setup>
import { computed } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

const props = defineProps({
  isAdmin: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  pendingRegistrations: { type: Number, default: 0 },
  upcomingEvents: { type: Number, default: 0 },
  contentItems: { type: Number, default: 0 },
  builds: { type: Number, default: 0 },
  users: { type: Number, default: 0 },
  logSummary: { type: Object, default: () => ({ total_events: 0, unique_ips: 0, threat_counts: {} }) },
  ipBlockSummary: { type: Object, default: () => ({ active: 0 }) },
  nextEvent: { type: Object, default: null },
  oldestPendingRequest: { type: Object, default: null },
})

const emit = defineEmits(['navigate', 'refresh'])
const { locale, t } = useLocale()

const moderationCards = computed(() => [
  {
    tab: 'registrations',
    icon: 'inbox',
    label: t('admin.workspace.cards.registrations'),
    value: props.pendingRegistrations,
    hint: t('admin.workspace.cards.registrationsHint'),
    tone: props.pendingRegistrations > 0 ? 'accent' : '',
  },
  {
    tab: 'calendar',
    icon: 'calendar',
    label: t('admin.workspace.cards.calendar'),
    value: props.upcomingEvents,
    hint: t('admin.workspace.cards.calendarHint'),
  },
  {
    tab: 'content',
    icon: 'forum',
    label: t('admin.workspace.cards.content'),
    value: props.contentItems,
    hint: t('admin.workspace.cards.contentHint'),
  },
  {
    tab: 'builds',
    icon: 'builds',
    label: t('admin.workspace.cards.builds'),
    value: props.builds,
    hint: t('admin.workspace.cards.buildsHint'),
  },
])

const adminCards = computed(() => [
  {
    tab: 'logs',
    icon: 'activity',
    label: t('admin.workspace.cards.logErrors'),
    value: (props.logSummary.threat_counts?.elevated || 0) + (props.logSummary.threat_counts?.critical || 0),
    hint: t('admin.workspace.cards.logErrorsHint', { total: props.logSummary.total_events || 0 }),
    tone: (props.logSummary.threat_counts?.critical || 0) > 0 ? 'danger' : '',
  },
  {
    tab: 'ip-blocks',
    icon: 'lock',
    label: t('admin.workspace.cards.ipBlocks'),
    value: props.ipBlockSummary.active || 0,
    hint: t('admin.workspace.cards.ipBlocksHint'),
  },
  {
    tab: 'users',
    icon: 'users',
    label: t('admin.workspace.cards.accounts'),
    value: props.users,
    hint: t('admin.workspace.cards.accountsHint'),
  },
])

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
</script>

<template>
  <section class="staff-overview-panel" :aria-label="t('admin.workspace.overviewTitle')">
    <div class="admin-panel-heading staff-overview-heading">
      <div>
        <span class="command-deck-eyebrow">{{ t('admin.workspace.eyebrow') }}</span>
        <h2>{{ t('admin.workspace.overviewTitle') }}</h2>
        <p>{{ isAdmin ? t('admin.workspace.adminOverviewHint') : t('admin.workspace.moderatorOverviewHint') }}</p>
      </div>
      <div class="hero-actions">
        <span class="summary-pill"><AppIcon :name="isAdmin ? 'shield' : 'user'" :size="15" />{{ isAdmin ? t('roles.admin') : t('roles.moderator') }}</span>
        <button class="small-action" type="button" :disabled="loading" @click="emit('refresh')">{{ t('admin.logs.refresh') }}</button>
      </div>
    </div>

    <section class="staff-priority-board">
      <header class="staff-priority-heading">
        <div><span>{{ t('admin.workspace.queueEyebrow') }}</span><h3>{{ t('admin.workspace.overviewTitle') }}</h3></div>
      </header>
      <button class="staff-priority-row" type="button" @click="emit('navigate', 'registrations')">
        <span class="staff-priority-icon" :class="{ 'has-work': oldestPendingRequest }"><AppIcon name="inbox" :size="19" /></span>
        <span class="staff-priority-copy">
          <strong>{{ t('admin.workspace.accessQueue') }}</strong>
          <small v-if="oldestPendingRequest">{{ oldestPendingRequest.display_name }} · {{ oldestPendingRequest.username }}</small>
          <small v-else>{{ t('admin.workspace.noPendingRequests') }}</small>
        </span>
        <time v-if="oldestPendingRequest">{{ t('admin.workspace.requestSince', { date: formatDateTime(oldestPendingRequest.created_at) }) }}</time>
        <AppIcon name="chevron-right" :size="16" />
      </button>
      <button class="staff-priority-row" type="button" @click="emit('navigate', 'calendar')">
        <span class="staff-priority-icon"><AppIcon name="calendar" :size="19" /></span>
        <span class="staff-priority-copy">
          <strong>{{ t('admin.workspace.nextEvent') }}</strong>
          <small v-if="nextEvent">{{ nextEvent.title }} · {{ t(`calendar.categories.${nextEvent.category}`) }}</small>
          <small v-else>{{ t('admin.workspace.noUpcomingEvents') }}</small>
        </span>
        <time v-if="nextEvent">{{ formatDateTime(nextEvent.start_at) }}</time>
        <AppIcon name="chevron-right" :size="16" />
      </button>
    </section>

    <section class="staff-overview-section">
      <div class="staff-overview-section-head">
        <div><span>{{ t('admin.workspace.moderationGroup') }}</span><strong>{{ t('admin.workspace.moderationTitle') }}</strong></div>
        <small>{{ t('admin.workspace.moderationHint') }}</small>
      </div>
      <div class="staff-overview-metric-band">
        <button v-for="card in moderationCards" :key="card.tab" :class="[`tone-${card.tone || 'default'}`]" type="button" @click="emit('navigate', card.tab)">
          <AppIcon :name="card.icon" :size="18" />
          <span><small>{{ card.label }}</small><strong>{{ card.value }}</strong><em>{{ card.hint }}</em></span>
        </button>
      </div>
    </section>

    <section v-if="isAdmin" class="staff-overview-section is-admin-scope">
      <div class="staff-overview-section-head">
        <div><span>{{ t('admin.workspace.adminGroup') }}</span><strong>{{ t('admin.workspace.adminTitle') }}</strong></div>
        <small>{{ t('admin.workspace.adminHint') }}</small>
      </div>
      <div class="staff-overview-metric-band is-admin-band">
        <button v-for="card in adminCards" :key="card.tab" :class="[`tone-${card.tone || 'default'}`]" type="button" @click="emit('navigate', card.tab)">
          <AppIcon :name="card.icon" :size="18" />
          <span><small>{{ card.label }}</small><strong>{{ card.value }}</strong><em>{{ card.hint }}</em></span>
        </button>
      </div>
    </section>

    <aside class="staff-role-scope-note" :class="{ 'is-admin': isAdmin }">
      <AppIcon :name="isAdmin ? 'shield' : 'lock'" :size="19" />
      <div>
        <strong>{{ isAdmin ? t('admin.workspace.adminScopeTitle') : t('admin.workspace.moderatorScopeTitle') }}</strong>
        <span>{{ isAdmin ? t('admin.workspace.adminScopeText') : t('admin.workspace.moderatorScopeText') }}</span>
      </div>
    </aside>
  </section>
</template>
