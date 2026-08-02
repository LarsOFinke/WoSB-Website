<script setup>
import { computed, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { getSecurityDashboard } from '@/modules/admin/api/admin'

const props = defineProps({
  fromDate: { type: String, default: '' },
  toDate: { type: String, default: '' },
  threatLevel: { type: String, default: '' },
  selectedIp: { type: String, default: '' },
  canBlock: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:fromDate',
  'update:toDate',
  'update:threatLevel',
  'update:selectedIp',
  'dashboard-update',
  'block-ip',
])

const { locale, t } = useLocale()
const sort = ref('threat')
const loading = ref(false)
const error = ref('')
let loadSequence = 0

const dashboard = ref({
  threat_score: 0,
  threat_level: 'low',
  total_events: 0,
  unique_ips: 0,
  threat_counts: { low: 0, guarded: 0, elevated: 0, critical: 0 },
  signal_counts: { reconnaissance: 0, login_failure: 0, rate_limit: 0 },
  days: [],
  ips: [],
})

const threatLevels = ['low', 'guarded', 'elevated', 'critical']
const threatLabel = computed(() => t(`admin.security.levels.${dashboard.value.threat_level || 'low'}`))
const ipOptions = computed(() => dashboard.value.ips || [])
const focusedIpRow = computed(() => ipOptions.value.find((row) => row.client_ip === props.selectedIp) || null)
const topIpRows = computed(() => ipOptions.value.slice(0, 5))
const maxDayEvents = computed(() => Math.max(1, ...(dashboard.value.days || []).map((day) => Number(day.total_events || 0))))
const threatCountTotal = computed(() => threatLevels.reduce((total, level) => total + Number(dashboard.value.threat_counts?.[level] || 0), 0))
const activeFilterCount = computed(() => [props.fromDate || props.toDate, props.threatLevel, props.selectedIp].filter(Boolean).length)

function isoDate(value) {
  return value.toISOString().slice(0, 10)
}

function formatDate(value) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(`${value}T00:00:00`))
}

function formatStoredDay(value) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(
    new Date(`${value}T00:00:00`),
  )
}

function setRange(days) {
  const end = new Date()
  const start = new Date(end)
  start.setDate(end.getDate() - Math.max(0, days - 1))
  emit('update:fromDate', isoDate(start))
  emit('update:toDate', isoDate(end))
}

function setExactDay(day) {
  emit('update:fromDate', day)
  emit('update:toDate', day)
}

function setThreat(level) {
  emit('update:threatLevel', props.threatLevel === level ? '' : level)
  if (props.selectedIp) emit('update:selectedIp', '')
}

function resetFilters() {
  setRange(7)
  emit('update:threatLevel', '')
  emit('update:selectedIp', '')
  sort.value = 'threat'
}

function dayBarStyle(day) {
  return { width: `${Math.max(2, (Number(day.total_events || 0) / maxDayEvents.value) * 100)}%` }
}

async function load() {
  const sequence = ++loadSequence
  loading.value = true
  error.value = ''
  try {
    const result = await getSecurityDashboard({
      fromDate: props.fromDate,
      toDate: props.toDate,
      threatLevel: props.threatLevel,
      clientIp: props.selectedIp,
      sort: sort.value,
      limit: 250,
    })
    if (sequence !== loadSequence) return
    dashboard.value = result
    emit('dashboard-update', result)
    const ips = result.ips || []
    if (props.selectedIp && !ips.some((row) => row.client_ip === props.selectedIp)) {
      emit('update:selectedIp', '')
    }
  } catch (err) {
    if (sequence !== loadSequence) return
    error.value = err.message || t('admin.security.loadError')
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

watch(
  () => [props.fromDate, props.toDate, props.threatLevel, props.selectedIp, sort.value],
  load,
  { immediate: true },
)
</script>

<template>
  <section class="security-dashboard" :aria-label="t('admin.security.title')">
    <article class="security-surface security-overview-surface">
      <div class="security-surface-head security-dashboard-heading">
        <div>
          <h3>{{ t('admin.security.title') }}</h3>
          <p>{{ t('admin.security.subtitle') }}</p>
        </div>
        <div class="security-heading-actions">
          <span class="summary-pill">{{ t('admin.security.activeFilters', { count: activeFilterCount }) }}</span>
          <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
        </div>
      </div>

      <section class="security-filter-console" :aria-label="t('admin.security.filtersTitle')">
        <div class="security-filter-console-head">
          <div><h4>{{ t('admin.security.filtersTitle') }}</h4><p>{{ t('admin.security.filtersHint') }}</p></div>
          <button class="small-action security-reset-action" type="button" @click="resetFilters">{{ t('admin.security.resetFilters') }}</button>
        </div>

        <div class="security-filter-grid">
          <div class="security-filter-group security-date-filter-group">
            <span class="security-filter-label">{{ t('admin.security.quickRange') }}</span>
            <div class="security-quick-range-row">
              <button type="button" @click="setRange(1)">{{ t('admin.security.today') }}</button>
              <button type="button" @click="setRange(7)">{{ t('admin.security.sevenDays') }}</button>
            </div>
            <div class="security-date-inputs">
              <label><span>{{ t('admin.security.from') }}</span><input :value="fromDate" type="date" @input="emit('update:fromDate', $event.target.value)" /></label>
              <label><span>{{ t('admin.security.to') }}</span><input :value="toDate" type="date" @input="emit('update:toDate', $event.target.value)" /></label>
            </div>
          </div>

          <div class="security-filter-group security-threat-filter-group">
            <span class="security-filter-label">{{ t('admin.security.threatFilter') }}</span>
            <div class="security-threat-filter-row">
              <button type="button" :class="{ 'is-active': !threatLevel }" @click="setThreat('')">
                <span>{{ t('admin.security.allThreats') }}</span><strong>{{ threatCountTotal }}</strong>
              </button>
              <button v-for="level in threatLevels" :key="level" type="button" :class="[`threat-${level}`, { 'is-active': threatLevel === level }]" @click="setThreat(level)">
                <span>{{ t(`admin.security.levels.${level}`) }}</span><strong>{{ dashboard.threat_counts?.[level] || 0 }}</strong>
              </button>
            </div>
          </div>

          <div class="security-filter-group security-ip-filter-group">
            <label class="security-ip-picker">
              <span class="security-filter-label">{{ t('admin.security.ipFilter') }}</span>
              <select :value="selectedIp" @change="emit('update:selectedIp', $event.target.value)">
                <option value="">{{ t('admin.security.allIps') }}</option>
                <option v-for="row in ipOptions" :key="row.client_ip" :value="row.client_ip">
                  {{ row.client_ip }} · {{ t(`admin.security.levels.${row.threat_level}`) }} {{ row.threat_score }}/100 · {{ row.event_count }}
                </option>
              </select>
            </label>
            <label class="security-toolbar-field">
              <span class="security-filter-label">{{ t('admin.security.sort') }}</span>
              <select v-model="sort">
                <option value="threat">{{ t('admin.security.sortThreat') }}</option>
                <option value="events">{{ t('admin.security.sortEvents') }}</option>
                <option value="last_seen">{{ t('admin.security.sortRecent') }}</option>
                <option value="ip">{{ t('admin.security.sortIp') }}</option>
              </select>
            </label>
          </div>
        </div>
      </section>

      <p v-if="error" class="error-text table-state">{{ error }}</p>
      <p v-else-if="loading" class="muted table-state">{{ t('admin.security.loading') }}</p>

      <div class="security-metric-grid">
        <article class="security-threat-card" :class="`threat-${dashboard.threat_level}`"><span>{{ t('admin.security.currentThreat') }}</span><strong>{{ threatLabel }}</strong><small>{{ dashboard.threat_score }}/100</small></article>
        <article><span>{{ t('admin.security.events') }}</span><strong>{{ dashboard.total_events }}</strong><small>{{ t('admin.security.filteredView') }}</small></article>
        <article><span>{{ t('admin.security.uniqueIps') }}</span><strong>{{ dashboard.unique_ips }}</strong><small>{{ t('admin.security.matchingIps') }}</small></article>
        <article><span>{{ t('admin.security.reconnaissance') }}</span><strong>{{ dashboard.signal_counts?.reconnaissance || 0 }}</strong></article>
        <article><span>{{ t('admin.security.loginFailures') }}</span><strong>{{ dashboard.signal_counts?.login_failure || 0 }}</strong></article>
        <article><span>{{ t('admin.security.rateLimits') }}</span><strong>{{ dashboard.signal_counts?.rate_limit || 0 }}</strong></article>
      </div>

      <div class="security-analysis-grid">
        <section class="security-table-card security-day-card">
          <div class="security-card-head"><div><h4>{{ t('admin.security.byDay') }}</h4><p class="muted">{{ t('admin.security.clickDayHint') }}</p></div></div>
          <div class="responsive-table-shell">
            <table class="security-table compact-security-table security-day-table">
              <thead><tr><th>{{ t('admin.security.day') }}</th><th>{{ t('admin.security.events') }}</th><th>IPs</th><th>{{ t('admin.security.reconnaissance') }}</th><th>{{ t('admin.security.loginFailures') }}</th><th>{{ t('admin.security.rateLimits') }}</th></tr></thead>
              <tbody>
                <tr v-for="day in dashboard.days" :key="day.day" role="button" tabindex="0" @click="setExactDay(day.day)" @keydown.enter="setExactDay(day.day)" @keydown.space.prevent="setExactDay(day.day)">
                  <td>{{ formatDate(day.day) }}</td>
                  <td><strong>{{ day.total_events }}</strong><span class="security-day-bar"><i :style="dayBarStyle(day)"></i></span></td>
                  <td>{{ day.unique_ips }}</td><td>{{ day.reconnaissance }}</td><td>{{ day.login_failures }}</td><td>{{ day.rate_limits }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="security-table-card security-focus-card">
          <div class="security-card-head"><div><h4>{{ selectedIp ? t('admin.security.selectedIp') : t('admin.security.topMatches') }}</h4><p class="muted">{{ selectedIp ? t('admin.security.filteredView') : t('admin.security.chooseIpHint') }}</p></div></div>

          <div v-if="focusedIpRow" class="security-ip-focus-card security-ip-focus-card-stacked">
            <div class="security-ip-focus-head">
              <span class="threat-badge" :class="`threat-${focusedIpRow.threat_level}`">{{ focusedIpRow.threat_score }}</span>
              <div class="security-ip-focus-copy"><strong>{{ focusedIpRow.client_ip }}</strong><small>{{ t(`admin.security.levels.${focusedIpRow.threat_level}`) }} · {{ t('admin.security.lastSeen') }} {{ formatStoredDay(focusedIpRow.last_seen) }}</small></div>
              <button v-if="canBlock" class="small-action security-block-ip-action" type="button" @click="emit('block-ip', focusedIpRow.client_ip)">{{ t('admin.security.blockSelectedIp') }}</button>
            </div>
            <div class="security-ip-metrics">
              <div><span>{{ t('admin.security.events') }}</span><strong>{{ focusedIpRow.event_count }}</strong></div>
              <div><span>{{ t('admin.security.reconnaissance') }}</span><strong>{{ focusedIpRow.reconnaissance }}</strong></div>
              <div><span>{{ t('admin.security.loginFailures') }}</span><strong>{{ focusedIpRow.login_failures }}</strong></div>
              <div><span>{{ t('admin.security.rateLimits') }}</span><strong>{{ focusedIpRow.rate_limits }}</strong></div>
            </div>
          </div>

          <div v-else-if="topIpRows.length" class="security-top-ip-list">
            <button v-for="row in topIpRows" :key="row.client_ip" type="button" @click="emit('update:selectedIp', row.client_ip)">
              <span class="threat-badge" :class="`threat-${row.threat_level}`">{{ row.threat_score }}</span>
              <span class="security-top-ip-copy"><strong>{{ row.client_ip }}</strong><small>{{ row.event_count }} {{ t('admin.security.events').toLowerCase() }}</small></span>
              <span>{{ t(`admin.security.levels.${row.threat_level}`) }}</span>
            </button>
          </div>
          <p v-else class="muted table-state">{{ t('admin.security.noMatches') }}</p>
        </section>
      </div>

      <p class="muted security-method-note">{{ t('admin.security.methodNote') }}</p>
    </article>
  </section>
</template>
