<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { getSecurityDashboard } from '@/modules/admin/api/admin'

const emit = defineEmits(['select-ip'])
const { locale, t } = useLocale()

const today = new Date()
const weekAgo = new Date(today)
weekAgo.setDate(today.getDate() - 6)
const isoDate = (value) => value.toISOString().slice(0, 10)

const fromDate = ref(isoDate(weekAgo))
const toDate = ref(isoDate(today))
const sort = ref('threat')
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
  } catch (err) {
    error.value = err.message || t('admin.security.loadError')
  } finally {
    loading.value = false
  }
}

watch(sort, load)
onMounted(load)
</script>

<template>
  <section class="security-dashboard" :aria-label="t('admin.security.title')">
    <div class="admin-panel-heading security-dashboard-heading">
      <div>
        <h3>{{ t('admin.security.title') }}</h3>
        <p>{{ t('admin.security.subtitle') }}</p>
      </div>
      <div class="security-filter-row">
        <label><span>{{ t('admin.security.from') }}</span><input v-model="fromDate" type="date" /></label>
        <label><span>{{ t('admin.security.to') }}</span><input v-model="toDate" type="date" /></label>
        <label><span>{{ t('admin.security.sort') }}</span><select v-model="sort"><option value="threat">{{ t('admin.security.sortThreat') }}</option><option value="requests">{{ t('admin.security.sortRequests') }}</option><option value="last_seen">{{ t('admin.security.sortRecent') }}</option><option value="ip">{{ t('admin.security.sortIp') }}</option></select></label>
        <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
      </div>
    </div>

    <p v-if="error" class="error-text table-state">{{ error }}</p>
    <div class="security-metric-grid">
      <article class="security-threat-card" :class="`threat-${dashboard.threat_level}`"><span>{{ t('admin.security.currentThreat') }}</span><strong>{{ threatLabel }}</strong><small>{{ dashboard.threat_score }}/100</small></article>
      <article><span>{{ t('admin.security.requests') }}</span><strong>{{ dashboard.total_requests }}</strong></article>
      <article><span>{{ t('admin.security.uniqueIps') }}</span><strong>{{ dashboard.unique_ips }}</strong></article>
      <article><span>{{ t('admin.security.suspicious') }}</span><strong>{{ dashboard.suspicious_hits }}</strong></article>
      <article><span>4xx</span><strong>{{ dashboard.status_4xx }}</strong></article>
      <article><span>5xx</span><strong>{{ dashboard.status_5xx }}</strong></article>
    </div>

    <p v-if="loading" class="muted table-state">{{ t('admin.security.loading') }}</p>
    <template v-else>
      <div class="security-dashboard-grid">
        <section class="security-table-card">
          <h4>{{ t('admin.security.byDay') }}</h4>
          <div class="responsive-table-shell">
            <table class="security-table">
              <thead><tr><th>{{ t('admin.security.day') }}</th><th>{{ t('admin.security.requests') }}</th><th>IPs</th><th>4xx</th><th>5xx</th><th>{{ t('admin.security.suspicious') }}</th></tr></thead>
              <tbody><tr v-for="day in dashboard.days" :key="day.day"><td>{{ formatDate(day.day) }}</td><td>{{ day.total }}</td><td>{{ day.unique_ips }}</td><td>{{ day.status_4xx }}</td><td>{{ day.status_5xx }}</td><td>{{ day.suspicious }}</td></tr></tbody>
            </table>
          </div>
        </section>

        <section class="security-table-card security-ip-card">
          <h4>{{ t('admin.security.byIp') }}</h4>
          <p v-if="dashboard.ips.length === 0" class="muted table-state">{{ t('admin.security.noIps') }}</p>
          <div v-else class="security-ip-list">
            <button v-for="row in dashboard.ips" :key="row.client_ip" type="button" class="security-ip-row" @click="emit('select-ip', row.client_ip)">
              <span class="threat-badge" :class="`threat-${row.threat_level}`">{{ row.threat_score }}</span>
              <span class="security-ip-main"><strong>{{ row.client_ip }}</strong><small>{{ t(`admin.security.levels.${row.threat_level}`) }} · {{ row.request_count }} {{ t('admin.security.requests').toLowerCase() }} · {{ row.distinct_paths }} {{ t('admin.security.paths') }}</small><small>{{ row.top_paths.join(' · ') }}</small></span>
              <span class="security-ip-meta"><strong>{{ row.suspicious_hits }} / {{ row.status_4xx }} / {{ row.status_5xx }}</strong><small>{{ t('admin.security.lastSeen') }} {{ formatDateTime(row.last_seen) }}</small></span>
            </button>
          </div>
        </section>
      </div>
    </template>
    <p class="muted security-method-note">{{ t('admin.security.methodNote') }}</p>
  </section>
</template>
