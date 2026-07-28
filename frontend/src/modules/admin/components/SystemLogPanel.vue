<script setup>
import { computed, ref, watch } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import SecurityLogDashboard from '@/modules/admin/components/SecurityLogDashboard.vue'

const props = defineProps({
  workspace: { type: Object, required: true },
})

const emit = defineEmits(['block-ip'])
const { locale, t } = useLocale()
const expandedLogId = ref(null)
const pendingEntryDeleteId = ref(null)
const confirmFilteredDelete = ref(false)

function model(key) {
  return computed({
    get: () => props.workspace[key].value,
    set: (value) => { props.workspace[key].value = value },
  })
}

const appLogs = model('appLogs')
const logSummary = model('logSummary')
const logLevel = model('logLevel')
const logPath = model('logPath')
const logIp = model('logIp')
const logThreat = model('logThreat')
const logFromDate = model('logFromDate')
const logToDate = model('logToDate')
const logIncludeBlocked = model('logIncludeBlocked')
const logSort = model('logSort')
const logOrder = model('logOrder')
const logsLoading = model('logsLoading')
const logsDeleting = model('logsDeleting')
const logsError = model('logsError')
const logsActionError = model('logsActionError')
const logsActionSuccess = model('logsActionSuccess')
const logsCountLabel = computed(() => props.workspace.logsCountLabel.value)
const activeLogFilterCount = computed(() => [
  logLevel.value,
  logPath.value,
  logIp.value,
  logThreat.value,
  logIncludeBlocked.value,
].filter(Boolean).length)

function isoDate(value) {
  return value.toISOString().slice(0, 10)
}

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

function setLogRange(days) {
  const end = new Date()
  const start = new Date(end)
  start.setDate(end.getDate() - Math.max(0, days - 1))
  logFromDate.value = isoDate(start)
  logToDate.value = isoDate(end)
}

function resetLogFilters() {
  logLevel.value = ''
  logPath.value = ''
  logIp.value = ''
  logThreat.value = ''
  logIncludeBlocked.value = false
  logSort.value = 'created_at'
  logOrder.value = 'desc'
  setLogRange(7)
}

function toggleEntry(entryId) {
  expandedLogId.value = expandedLogId.value === entryId ? null : entryId
  pendingEntryDeleteId.value = null
}

async function confirmDeleteEntry(entryId) {
  const deleted = await props.workspace.deleteLogEntry(entryId)
  if (deleted) {
    pendingEntryDeleteId.value = null
    if (expandedLogId.value === entryId) expandedLogId.value = null
  }
}

async function confirmDeleteFiltered() {
  const result = await props.workspace.deleteFilteredLogs()
  if (result >= 0) {
    confirmFilteredDelete.value = false
    expandedLogId.value = null
    pendingEntryDeleteId.value = null
  }
}

function openBlockManager(ipAddress) {
  emit('block-ip', ipAddress)
}

watch(appLogs, (rows) => {
  if (expandedLogId.value && !rows.some((row) => row.id === expandedLogId.value)) {
    expandedLogId.value = null
  }
})
</script>

<template>
  <section class="system-log-panel">
    <div class="admin-panel-heading system-log-heading">
      <div>
        <h2>{{ t('admin.logs.title') }}</h2>
        <p>{{ t('admin.logs.subtitle') }}</p>
      </div>
      <div class="system-log-heading-actions">
        <span class="summary-pill">{{ logsCountLabel }}</span>
        <button class="small-action" type="button" :disabled="logsLoading || logsDeleting" @click="workspace.loadLogs">
          {{ t('admin.logs.refresh') }}
        </button>
        <button
          class="danger-action"
          type="button"
          :disabled="logsLoading || logsDeleting || logSummary.total === 0"
          @click="confirmFilteredDelete = true"
        >
          {{ t('admin.logs.deleteFiltered') }}
        </button>
      </div>
    </div>

    <div v-if="confirmFilteredDelete" class="system-log-delete-confirmation" role="alert">
      <div>
        <strong>{{ t('admin.logs.deleteFilteredConfirmTitle') }}</strong>
        <p>{{ t('admin.logs.deleteFilteredConfirmText', { count: logSummary.total }) }}</p>
      </div>
      <div class="hero-actions">
        <button class="danger-action" type="button" :disabled="logsDeleting" @click="confirmDeleteFiltered">
          {{ logsDeleting ? t('admin.logs.deleting') : t('admin.logs.deleteNow') }}
        </button>
        <button class="small-action" type="button" :disabled="logsDeleting" @click="confirmFilteredDelete = false">
          {{ t('common.cancel') }}
        </button>
      </div>
    </div>

    <p v-if="logsActionError" class="error-text table-state">{{ logsActionError }}</p>
    <p v-else-if="logsActionSuccess" class="success-text table-state">{{ logsActionSuccess }}</p>

    <div class="staff-log-workspace">
      <div class="staff-log-summary-strip">
        <article><span>{{ t('admin.logs.errors') }}</span><strong>{{ logSummary.errors }}</strong></article>
        <article><span>{{ t('admin.logs.warnings') }}</span><strong>{{ logSummary.warnings }}</strong></article>
        <article><span>{{ t('admin.logs.slowRequests') }}</span><strong>{{ logSummary.slow_requests }}</strong></article>
        <article><span>{{ t('admin.security.activeFilters', { count: activeLogFilterCount }) }}</span><strong>{{ logSummary.total }}</strong></article>
      </div>

      <article class="staff-log-surface log-filter-surface system-log-filter-surface">
        <div class="staff-log-surface-head">
          <div>
            <h3>{{ t('admin.logs.requestFilters') }}</h3>
            <p>{{ t('admin.logs.requestFiltersHint') }}</p>
          </div>
          <button class="small-action" type="button" @click="resetLogFilters">{{ t('admin.security.resetFilters') }}</button>
        </div>

        <div class="staff-log-quick-range" :aria-label="t('admin.security.quickRange')">
          <button type="button" @click="setLogRange(1)">{{ t('admin.security.today') }}</button>
          <button type="button" @click="setLogRange(7)">{{ t('admin.security.sevenDays') }}</button>
          <button type="button" @click="setLogRange(30)">{{ t('admin.security.thirtyDays') }}</button>
        </div>

        <div class="system-log-filter-grid">
          <label class="system-log-field">
            <span>{{ t('admin.security.from') }}</span>
            <input v-model="logFromDate" type="date" />
          </label>
          <label class="system-log-field">
            <span>{{ t('admin.security.to') }}</span>
            <input v-model="logToDate" type="date" />
          </label>
          <label class="system-log-field">
            <span>{{ t('admin.logs.levelLabel') }}</span>
            <select v-model="logLevel">
              <option value="">{{ t('admin.logs.levelAll') }}</option>
              <option>INFO</option><option>WARNING</option><option>ERROR</option><option>CRITICAL</option>
            </select>
          </label>
          <label class="system-log-field">
            <span>{{ t('admin.security.threatFilter') }}</span>
            <select v-model="logThreat">
              <option value="">{{ t('admin.security.allThreats') }}</option>
              <option value="low">{{ t('admin.security.levels.low') }}</option>
              <option value="guarded">{{ t('admin.security.levels.guarded') }}</option>
              <option value="elevated">{{ t('admin.security.levels.elevated') }}</option>
              <option value="critical">{{ t('admin.security.levels.critical') }}</option>
            </select>
          </label>
          <label class="system-log-field system-log-field--wide">
            <span>{{ t('admin.logs.pathLabel') }}</span>
            <input v-model="logPath" type="search" :placeholder="t('admin.logs.pathPlaceholder')" />
          </label>
          <label class="system-log-field system-log-field--wide">
            <span>{{ t('admin.logs.ipLabel') }}</span>
            <input v-model="logIp" type="search" :placeholder="t('admin.security.ipFilter')" />
          </label>
          <label class="system-log-field">
            <span>{{ t('admin.logs.sortLabel') }}</span>
            <select v-model="logSort">
              <option value="created_at">{{ t('admin.logs.sortDate') }}</option>
              <option value="ip">{{ t('admin.logs.sortIp') }}</option>
              <option value="status">{{ t('admin.logs.sortStatus') }}</option>
              <option value="duration">{{ t('admin.logs.sortDuration') }}</option>
              <option value="level">{{ t('admin.logs.sortLevel') }}</option>
            </select>
          </label>
          <label class="system-log-field">
            <span>{{ t('admin.logs.orderLabel') }}</span>
            <select v-model="logOrder">
              <option value="desc">{{ t('admin.logs.desc') }}</option>
              <option value="asc">{{ t('admin.logs.asc') }}</option>
            </select>
          </label>
        </div>

        <label class="system-log-blocked-toggle">
          <input v-model="logIncludeBlocked" type="checkbox" />
          <span>
            <strong>{{ t('admin.logs.includeBlocked') }}</strong>
            <small>{{ t('admin.logs.includeBlockedHint') }}</small>
          </span>
        </label>

        <div class="staff-log-active-scope" aria-live="polite">
          <strong>{{ logFromDate }} – {{ logToDate }}</strong>
          <strong v-if="!logIncludeBlocked">{{ t('admin.logs.blockedHidden') }}</strong>
          <strong v-if="logThreat">{{ t(`admin.security.levels.${logThreat}`) }}</strong>
          <strong v-if="logIp">{{ logIp }}</strong>
          <strong v-if="logLevel">{{ logLevel }}</strong>
          <strong v-if="logPath">{{ logPath }}</strong>
        </div>
      </article>

      <article class="staff-log-surface log-results-surface">
        <div class="staff-log-surface-head">
          <div><h3>{{ t('admin.logs.resultsTitle') }}</h3><p>{{ t('admin.logs.resultsHint') }}</p></div>
          <span class="summary-pill">{{ t('admin.logs.total') }} · {{ logSummary.total }}</span>
        </div>
        <p v-if="logsLoading" class="muted table-state">{{ t('admin.logs.loading') }}</p>
        <p v-else-if="logsError" class="error-text table-state">{{ logsError }}</p>
        <p v-else-if="appLogs.length === 0" class="muted table-state">{{ t('admin.logs.empty') }}</p>
        <div v-else class="staff-log-list">
          <article
            v-for="entry in appLogs"
            :key="entry.id"
            class="staff-log-entry"
            :class="[`level-${(entry.level || 'info').toLowerCase()}`, { 'is-open': expandedLogId === entry.id }]"
          >
            <button class="staff-log-entry-summary" type="button" :aria-expanded="expandedLogId === entry.id" @click="toggleEntry(entry.id)">
              <time>{{ formatDateTime(entry.created_at) }}</time>
              <span class="staff-log-level-badge" :class="`level-${(entry.level || '').toLowerCase()}`">{{ entry.level }}</span>
              <span class="staff-log-request">
                <strong>{{ entry.method || entry.logger }} <code>{{ entry.path || '—' }}</code></strong>
                <small>{{ entry.message || entry.client_ip || '—' }}</small>
              </span>
              <span class="staff-log-response">
                <b :class="{ 'is-error': Number(entry.status_code) >= 400 }">{{ entry.status_code || '—' }}</b>
                <small>{{ workspace.formatDuration(entry.duration_ms) }}</small>
              </span>
              <AppIcon name="chevron-right" :size="16" />
            </button>
            <div v-if="expandedLogId === entry.id" class="staff-log-entry-details">
              <dl>
                <div><dt>{{ t('admin.logs.requestId') }}</dt><dd>{{ entry.request_id || '—' }}</dd></div>
                <div><dt>{{ t('logs.clientIp') }}</dt><dd>{{ entry.client_ip || '—' }}</dd></div>
                <div><dt>{{ t('logs.queryString') }}</dt><dd>{{ entry.query_string || '—' }}</dd></div>
                <div><dt>User-Agent</dt><dd>{{ entry.user_agent || '—' }}</dd></div>
                <div><dt>Logger</dt><dd>{{ entry.logger || '—' }}</dd></div>
              </dl>
              <div class="staff-log-entry-message">
                <strong>{{ t('admin.logs.details') }}</strong>
                <p :class="{ 'error-text': entry.exception }">{{ entry.exception || entry.message || '—' }}</p>
                <div class="system-log-entry-actions">
                  <div v-if="entry.client_ip" class="hero-actions">
                    <button class="small-action" type="button" @click="openBlockManager(entry.client_ip)">{{ t('admin.ipBlocks.blockAction') }}</button>
                    <button class="small-action" type="button" @click="workspace.openLogsForIp(entry.client_ip)">{{ t('admin.ipBlocks.viewLogs') }}</button>
                  </div>
                  <div v-if="pendingEntryDeleteId === entry.id" class="system-log-entry-delete-confirmation">
                    <span>{{ t('admin.logs.deleteOneConfirm') }}</span>
                    <button class="danger-action" type="button" :disabled="logsDeleting" @click="confirmDeleteEntry(entry.id)">{{ t('admin.logs.deleteNow') }}</button>
                    <button class="small-action" type="button" :disabled="logsDeleting" @click="pendingEntryDeleteId = null">{{ t('common.cancel') }}</button>
                  </div>
                  <button v-else class="danger-action" type="button" :disabled="logsDeleting" @click="pendingEntryDeleteId = entry.id">
                    {{ t('admin.logs.deleteOne') }}
                  </button>
                </div>
              </div>
            </div>
          </article>
        </div>
      </article>

      <details class="staff-log-security-disclosure">
        <summary>
          <span>{{ t('admin.security.title') }}</span>
          <small>{{ t('admin.security.subtitle') }}</small>
          <AppIcon name="chevron-right" :size="17" />
        </summary>
        <SecurityLogDashboard
          v-model:from-date="logFromDate"
          v-model:to-date="logToDate"
          v-model:threat-level="logThreat"
          v-model:selected-ip="logIp"
          :include-blocked="logIncludeBlocked"
          :can-block="true"
          @block-ip="openBlockManager"
        />
      </details>
    </div>
  </section>
</template>
