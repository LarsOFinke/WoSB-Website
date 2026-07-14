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
  logSummary: { type: Object, default: () => ({ total: 0, errors: 0, warnings: 0 }) },
  ipBlockSummary: { type: Object, default: () => ({ active: 0 }) },
  webhookSummary: { type: Object, default: () => ({ active: 0, failing: 0 }) },
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
    value: props.logSummary.errors || 0,
    hint: t('admin.workspace.cards.logErrorsHint', { total: props.logSummary.total || 0 }),
    tone: props.logSummary.errors > 0 ? 'danger' : '',
  },
  {
    tab: 'ip-blocks',
    icon: 'lock',
    label: t('admin.workspace.cards.ipBlocks'),
    value: props.ipBlockSummary.active || 0,
    hint: t('admin.workspace.cards.ipBlocksHint'),
  },
  {
    tab: 'integrations',
    icon: 'spark',
    label: t('admin.workspace.cards.integrations'),
    value: props.webhookSummary.active || 0,
    hint: t('admin.workspace.cards.integrationsHint', { failing: props.webhookSummary.failing || 0 }),
    tone: props.webhookSummary.failing > 0 ? 'danger' : '',
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

    <section class="staff-overview-section">
      <div class="staff-overview-section-head">
        <div>
          <span>{{ t('admin.workspace.moderationGroup') }}</span>
          <strong>{{ t('admin.workspace.moderationTitle') }}</strong>
        </div>
        <small>{{ t('admin.workspace.moderationHint') }}</small>
      </div>
      <div class="staff-overview-card-grid">
        <button
          v-for="card in moderationCards"
          :key="card.tab"
          class="staff-overview-card"
          :class="[`tone-${card.tone || 'default'}`]"
          type="button"
          @click="emit('navigate', card.tab)"
        >
          <span class="staff-overview-card-icon"><AppIcon :name="card.icon" :size="20" /></span>
          <span class="staff-overview-card-copy"><small>{{ card.label }}</small><strong>{{ card.value }}</strong><span>{{ card.hint }}</span></span>
          <AppIcon class="staff-overview-card-arrow" name="arrow-right" :size="17" />
        </button>
      </div>
    </section>

    <section v-if="isAdmin" class="staff-overview-section is-admin-scope">
      <div class="staff-overview-section-head">
        <div>
          <span>{{ t('admin.workspace.adminGroup') }}</span>
          <strong>{{ t('admin.workspace.adminTitle') }}</strong>
        </div>
        <small>{{ t('admin.workspace.adminHint') }}</small>
      </div>
      <div class="staff-overview-card-grid">
        <button
          v-for="card in adminCards"
          :key="card.tab"
          class="staff-overview-card"
          :class="[`tone-${card.tone || 'default'}`]"
          type="button"
          @click="emit('navigate', card.tab)"
        >
          <span class="staff-overview-card-icon"><AppIcon :name="card.icon" :size="20" /></span>
          <span class="staff-overview-card-copy"><small>{{ card.label }}</small><strong>{{ card.value }}</strong><span>{{ card.hint }}</span></span>
          <AppIcon class="staff-overview-card-arrow" name="arrow-right" :size="17" />
        </button>
      </div>
    </section>

    <div class="staff-overview-queue-grid">
      <article class="staff-overview-queue-card">
        <div class="staff-overview-section-head compact">
          <div><span>{{ t('admin.workspace.queueEyebrow') }}</span><strong>{{ t('admin.workspace.accessQueue') }}</strong></div>
          <button class="small-action" type="button" @click="emit('navigate', 'registrations')">{{ t('admin.workspace.openArea') }}</button>
        </div>
        <template v-if="oldestPendingRequest">
          <strong>{{ oldestPendingRequest.display_name }}</strong>
          <span>{{ oldestPendingRequest.username }}</span>
          <small>{{ t('admin.workspace.requestSince', { date: formatDateTime(oldestPendingRequest.created_at) }) }}</small>
        </template>
        <p v-else class="muted">{{ t('admin.workspace.noPendingRequests') }}</p>
      </article>

      <article class="staff-overview-queue-card">
        <div class="staff-overview-section-head compact">
          <div><span>{{ t('admin.workspace.queueEyebrow') }}</span><strong>{{ t('admin.workspace.nextEvent') }}</strong></div>
          <button class="small-action" type="button" @click="emit('navigate', 'calendar')">{{ t('admin.workspace.openArea') }}</button>
        </div>
        <template v-if="nextEvent">
          <strong>{{ nextEvent.title }}</strong>
          <span>{{ t(`calendar.categories.${nextEvent.category}`) }}</span>
          <small>{{ formatDateTime(nextEvent.start_at) }}</small>
        </template>
        <p v-else class="muted">{{ t('admin.workspace.noUpcomingEvents') }}</p>
      </article>
    </div>

    <aside class="staff-role-scope-note" :class="{ 'is-admin': isAdmin }">
      <AppIcon :name="isAdmin ? 'shield' : 'lock'" :size="19" />
      <div>
        <strong>{{ isAdmin ? t('admin.workspace.adminScopeTitle') : t('admin.workspace.moderatorScopeTitle') }}</strong>
        <span>{{ isAdmin ? t('admin.workspace.adminScopeText') : t('admin.workspace.moderatorScopeText') }}</span>
      </div>
    </aside>
  </section>
</template>
