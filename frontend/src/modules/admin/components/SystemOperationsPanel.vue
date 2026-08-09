<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getSystemUpdateStatus, requestSystemUpdate } from '@/modules/admin/api/admin'
import HostCapabilityField from '@/modules/admin/components/HostCapabilityField.vue'

const props = defineProps({
  apiStatus: { type: String, required: true },
  apiStatusDetail: { type: String, required: true },
})

const emit = defineEmits(['refresh-api'])
const { locale, t } = useLocale()
const update = ref({ state: 'idle', operation: 'update', message: '', request_available: false })
const loading = ref(false)
const error = ref('')
const hostApproval = ref('')
let pollTimer = null

const inProgress = computed(() => ['queued', 'running'].includes(update.value.state))
const stateLabel = computed(() => t(`admin.system.states.${update.value.state || 'idle'}`))
const operationLabel = computed(() => t(`admin.system.operations.${update.value.operation || 'update'}`))
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

async function requestOperation(operation) {
  if (!update.value.request_available || inProgress.value) return
  const confirmationKey = operation === 'restart'
    ? 'restartConfirm'
    : operation === 'rollback' ? 'rollbackConfirm' : 'updateConfirm'
  if (!window.confirm(t(`admin.system.${confirmationKey}`))) return
  loading.value = true
  error.value = ''
  try {
    update.value = (await requestSystemUpdate(operation, hostApproval.value)).status
    hostApproval.value = ''
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

    <article class="home-status-card refined-status-card system-operation-card system-update-card" aria-live="polite">
      <span>{{ t('admin.system.updateTitle') }}</span>
      <strong>{{ stateLabel }}</strong>
      <p>{{ update.message || t('admin.system.updateText') }}</p>
      <dl class="system-update-meta">
        <div><dt>{{ t('admin.system.operation') }}</dt><dd>{{ operationLabel }}</dd></div>
        <div><dt>{{ t('admin.system.startedAt') }}</dt><dd>{{ formatDateTime(update.started_at) }}</dd></div>
        <div><dt>{{ t('admin.system.finishedAt') }}</dt><dd>{{ formatDateTime(update.finished_at) }}</dd></div>
      </dl>
      <small>Updates use only verified artifacts from the protected host inbox
        directory; backups, migrations, and readiness checks run before activation.</small>
      <HostCapabilityField v-model="hostApproval" />
      <div class="system-update-actions">
        <button class="primary-action" type="button" :disabled="loading || !update.request_available || inProgress || hostApproval.length < 24" @click="requestOperation('update')">
          {{ inProgress ? t('admin.system.updateRunning') : t('admin.system.updateButton') }}
        </button>
        <button class="secondary-action" type="button" :disabled="loading || !update.request_available || inProgress || hostApproval.length < 24" @click="requestOperation('restart')">
          {{ t('admin.system.restartButton') }}
        </button>
        <button class="secondary-action" type="button" :disabled="loading || !update.request_available || inProgress || hostApproval.length < 24" @click="requestOperation('rollback')">
          {{ t('admin.system.rollbackButton') }}
        </button>
      </div>
    </article>
  </div>

  <p v-if="error" class="error-text table-state">{{ error }}</p>

</template>
