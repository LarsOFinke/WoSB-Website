<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { MONITORING_HTTPS_PORT } from '@/config/runtime'
import { useLocale } from '@/locales'
import { getSystemUpdateStatus, requestSystemUpdate } from '@/modules/admin/api/admin'

const props = defineProps({
  apiStatus: { type: String, required: true },
  apiStatusDetail: { type: String, required: true },
  isAdmin: { type: Boolean, default: false },
})

const emit = defineEmits(['refresh-api'])
const { locale, t } = useLocale()
const update = ref({ state: 'idle', operation: 'update', message: '', request_available: false })
const loading = ref(false)
const error = ref('')
const success = ref('')
let pollTimer = null

const inProgress = computed(() => ['queued', 'running'].includes(update.value.state))
const stateLabel = computed(() => t(`admin.system.states.${update.value.state || 'idle'}`))
const operationLabel = computed(() => t(`admin.system.operations.${update.value.operation || 'update'}`))
const monitoringUrl = computed(() => {
  if (typeof window === 'undefined') return `https://royal-blackwater-fleet.eu:${MONITORING_HTTPS_PORT}`
  return `https://${window.location.hostname}:${MONITORING_HTTPS_PORT}`
})

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function schedulePoll() {
  window.clearTimeout(pollTimer)
  if (!inProgress.value) return
  pollTimer = window.setTimeout(async () => {
    await loadUpdate()
    schedulePoll()
  }, 3000)
}

async function loadUpdate() {
  loading.value = true
  error.value = ''
  try {
    update.value = await getSystemUpdateStatus()
  } catch (err) {
    error.value = err.message || t('admin.system.loadError')
  } finally {
    loading.value = false
  }
}

async function refresh() {
  emit('refresh-api')
  await loadUpdate()
  schedulePoll()
}

async function trigger(operation) {
  if (!props.isAdmin || inProgress.value) return
  const confirmKey = {
    restart: 'admin.system.restartConfirm',
    update: 'admin.system.updateConfirm',
    rollback: 'admin.system.rollbackConfirm',
  }[operation]
  if (confirmKey && !window.confirm(t(confirmKey))) return

  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await requestSystemUpdate(operation)
    update.value = response.status
    const successKey = {
      restart: 'admin.system.restartRequestAccepted',
      update: 'admin.system.requestAccepted',
      rollback: 'admin.system.rollbackRequestAccepted',
    }[operation] || 'admin.system.requestAccepted'
    success.value = t(successKey)
    schedulePoll()
  } catch (err) {
    error.value = err.message || t('admin.system.requestError')
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
onUnmounted(() => window.clearTimeout(pollTimer))
</script>

<template>
  <div class="admin-panel-heading">
    <div><h2>{{ t('admin.status.title') }}</h2><p>{{ t('admin.status.subtitle') }}</p></div>
    <button class="small-action" type="button" :disabled="loading" @click="refresh">{{ t('admin.system.refresh') }}</button>
  </div>

  <div class="system-status-grid">
    <aside class="home-status-card refined-status-card admin-status-card" aria-live="polite">
      <span>{{ t('admin.status.cardLabel') }}</span><strong>{{ apiStatus }}</strong><p>{{ apiStatusDetail }}</p>
    </aside>

    <article class="home-status-card refined-status-card system-operation-card">
      <span>{{ t('admin.system.monitoringTitle') }}</span>
      <strong>HTTPS · {{ MONITORING_HTTPS_PORT }}</strong>
      <p>{{ t('admin.system.monitoringText') }}</p>
      <small>{{ t('admin.system.httpsHint') }}</small>
      <a class="button-box" :href="monitoringUrl" target="_blank" rel="noopener">{{ t('admin.system.openMonitoring') }}</a>
    </article>

    <article class="home-status-card refined-status-card system-operation-card system-update-card" aria-live="polite">
      <span>{{ t('admin.system.updateTitle') }}</span>
      <strong>{{ stateLabel }}</strong>
      <p>{{ update.message || t('admin.system.updateText') }}</p>
      <dl class="system-update-meta">
        <div><dt>{{ t('admin.system.operation') }}</dt><dd>{{ operationLabel }}</dd></div>
        <div><dt>{{ t('admin.system.startedAt') }}</dt><dd>{{ formatDateTime(update.started_at) }}</dd></div>
        <div><dt>{{ t('admin.system.finishedAt') }}</dt><dd>{{ formatDateTime(update.finished_at) }}</dd></div>
      </dl>
      <div v-if="isAdmin" class="system-update-actions">
        <button class="form-button danger-action system-restart-action" type="button" :disabled="loading || inProgress || !update.request_available" @click="trigger('restart')">
          {{ t('admin.system.restartButton') }}
        </button>
        <button class="form-button primary-action" type="button" :disabled="loading || inProgress || !update.request_available" @click="trigger('update')">
          {{ inProgress ? t('admin.system.updateRunning') : t('admin.system.updateButton') }}
        </button>
        <button class="form-button secondary-action" type="button" :disabled="loading || inProgress || !update.request_available" @click="trigger('rollback')">
          {{ t('admin.system.rollbackButton') }}
        </button>
      </div>
      <small v-else>{{ t('admin.system.adminOnly') }}</small>
    </article>
  </div>

  <p v-if="success" class="success-text table-state">{{ success }}</p>
  <p v-if="error" class="error-text table-state">{{ error }}</p>

</template>
