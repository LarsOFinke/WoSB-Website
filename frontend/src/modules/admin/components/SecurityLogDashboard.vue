<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { getSecurityDashboard } from '@/modules/admin/api/admin'

const emit = defineEmits(['select-ip', 'ip-options'])
const { locale, t } = useLocale()

const today = new Date()
const weekAgo = new Date(today)
weekAgo.setDate(today.getDate() - 6)
const isoDate = (value) => value.toISOString().slice(0, 10)

const fromDate = ref(isoDate(weekAgo))
const toDate = ref(isoDate(today))
const sort = ref('threat')
const selectedIp = ref('')
const loading = ref(false)
const error = ref('')
const dashboard = ref({
  threat_score: 0,
  threat_level: 'low',
  total_requests: 0,
  unique_ips: 0,
  suspicious_hits: 0,
  status_4xx: 0,
  status_5xx: 0,
  days: [],
  ips: [],
})

const threatLabel = computed(() => t(`admin.security.levels.${dashboard.value.threat_level || 'low'}`))
const ipOptions = computed(() => dashboard.value.ips || [])
const focusedIpRow = computed(() => {
  if (!selectedIp.value) return null
  return ipOptions.value.find((row) => row.client_ip === selectedIp.value) || null
})

function formatDate(value) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(`${value}T00:00:00`))
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await getSecurityDashboard({
      fromDate: fromDate.value,
      toDate: toDate.value,
      sort: sort.value,
      limit: 100,
    })
    const ips = dashboard.value.ips || []
    emit('ip-options', ips)
    if (selectedIp.value && !ips.some((row) => row.client_ip === selectedIp.value)) {
      selectedIp.value = ''
    }
  } catch (err) {
    error.value = err.message || t('admin.security.loadError')
    emit('ip-options', [])
  } finally {
    loading.value = false
  }
}

watch(selectedIp, (value) => emit('select-ip', value))
onMounted(load)
</script>

<template>
  <section class="security-dashboard" :aria-label="t('admin.security.title')">
    <article class="security-surface security-overview-surface">
      <div class="security-surface-head security-dashboard-heading">
        <div>
          <h3>{{ t('admin.security.title') }}</h3>
          <p>{{ t('admin.security.subtitle') }}</p>
        </div>
        <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
      </div>

      <p v-if="error" class="error-text table-state">{{ error }}</p>
      <p v-else-if="loading" class="muted table-state">{{ t('admin.security.loading') }}</p>

      <div class="security-metric-grid">
        <article class="security-threat-card" :class="`threat-${dashboard.threat_level}`">
          <span>{{ t('admin.security.currentThreat') }}</span>
          <strong>{{ threatLabel }}</strong>
          <small>{{ dashboard.threat_score }}/100</small>
        </article>
        <article>
          <span>{{ t('admin.security.requests') }}</span>
          <strong>{{ dashboard.total_requests }}</strong>
          <small>{{ t('admin.security.byDay') }}</small>
        </article>
        <article>
          <span>{{ t('admin.security.uniqueIps') }}</span>
          <strong>{{ dashboard.unique_ips }}</strong>
          <small>{{ t('admin.security.byIp') }}</small>
        </article>
        <article>
          <span>{{ t('admin.security.suspicious') }}</span>
          <strong>{{ dashboard.suspicious_hits }}</strong>
          <small>Probe / scan patterns</small>
        </article>
        <article>
          <span>4xx</span>
          <strong>{{ dashboard.status_4xx }}</strong>
          <small>Client-side errors</small>
        </article>
        <article>
          <span>5xx</span>
          <strong>{{ dashboard.status_5xx }}</strong>
          <small>Server-side errors</small>
        </article>
      </div>

      <section class="security-table-card security-day-card security-full-width-card">
        <div class="security-card-head security-card-head-with-controls">
          <div>
            <h4>{{ t('admin.security.byDay') }}</h4>
            <p class="muted">{{ t('admin.security.subtitle') }}</p>
          </div>
          <div class="security-date-controls">
            <label><span>{{ t('admin.security.from') }}</span><input v-model="fromDate" type="date" /></label>
            <label><span>{{ t('admin.security.to') }}</span><input v-model="toDate" type="date" /></label>
            <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
          </div>
        </div>
        <div class="responsive-table-shell">
          <table class="security-table compact-security-table">
            <thead>
              <tr>
                <th>{{ t('admin.security.day') }}</th>
                <th>{{ t('admin.security.requests') }}</th>
                <th>IPs</th>
                <th>4xx</th>
                <th>5xx</th>
                <th>{{ t('admin.security.suspicious') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in dashboard.days" :key="day.day">
                <td>{{ formatDate(day.day) }}</td>
                <td>{{ day.total }}</td>
                <td>{{ day.unique_ips }}</td>
                <td>{{ day.status_4xx }}</td>
                <td>{{ day.status_5xx }}</td>
                <td>{{ day.suspicious }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="security-table-card security-ip-card security-full-width-card">
        <div class="security-ip-card-header">
          <div>
            <h4>{{ t('admin.security.byIp') }}</h4>
            <p class="muted">{{ t('admin.security.methodNote') }}</p>
          </div>
          <label class="security-ip-picker">
            <span>{{ t('admin.security.byIp') }}</span>
            <select v-model="selectedIp">
              <option value="">{{ t('admin.security.allIps') }}</option>
              <option v-for="row in ipOptions" :key="row.client_ip" :value="row.client_ip">
                {{ row.client_ip }} · {{ t(`admin.security.levels.${row.threat_level}`) }} {{ row.threat_score }}/100 · {{ row.request_count }} {{ t('admin.security.requests').toLowerCase() }}
              </option>
            </select>
          </label>
        </div>

        <p v-if="dashboard.ips.length === 0" class="muted table-state">{{ t('admin.security.noIps') }}</p>
        <div v-else-if="focusedIpRow" class="security-ip-focus-card security-ip-focus-card-compact">
          <div class="security-ip-focus-head">
            <span class="threat-badge" :class="`threat-${focusedIpRow.threat_level}`">{{ focusedIpRow.threat_score }}</span>
            <div class="security-ip-focus-copy">
              <strong>{{ focusedIpRow.client_ip }}</strong>
              <small>{{ t(`admin.security.levels.${focusedIpRow.threat_level}`) }} · {{ t('admin.security.lastSeen') }} {{ formatDateTime(focusedIpRow.last_seen) }}</small>
            </div>
          </div>
          <div class="security-ip-metrics">
            <div><span>{{ t('admin.security.requests') }}</span><strong>{{ focusedIpRow.request_count }}</strong></div>
            <div><span>{{ t('admin.security.paths') }}</span><strong>{{ focusedIpRow.distinct_paths }}</strong></div>
            <div><span>{{ t('admin.security.suspicious') }}</span><strong>{{ focusedIpRow.suspicious_hits }}</strong></div>
            <div><span>4xx / 5xx</span><strong>{{ focusedIpRow.status_4xx }} / {{ focusedIpRow.status_5xx }}</strong></div>
          </div>
          <div class="security-path-pill-row">
            <span v-for="path in focusedIpRow.top_paths" :key="path" class="security-path-pill">{{ path }}</span>
          </div>
        </div>
        <p v-else class="muted security-ip-empty-focus">{{ t('admin.security.allIps') }} · {{ dashboard.unique_ips }} {{ t('admin.security.uniqueIps').toLowerCase() }}</p>
      </section>
    </article>
  </section>
</template>
