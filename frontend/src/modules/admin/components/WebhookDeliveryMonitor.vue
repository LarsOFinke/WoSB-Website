<script setup>
import { computed, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import {
  deleteOutboundWebhookDelivery,
  deleteOutboundWebhookDeliveryHistory,
  listOutboundWebhookDeliveries,
  retryOutboundWebhookDelivery,
} from '@/modules/admin/api/admin'

const props = defineProps({
  webhooks: { type: Array, default: () => [] },
  canManage: { type: Boolean, default: false },
  fixedEventType: { type: String, default: '' },
  events: { type: Array, default: () => [] },
})

const { locale, t } = useLocale()
const opened = ref(false)
const loading = ref(false)
const deleting = ref(false)
const error = ref('')
const success = ref('')
const deliveries = ref([])
const deliveryWebhook = ref('')
const deliveryStatus = ref('')
const deliveryEvent = ref(props.fixedEventType || '')
const pendingDeliveryDeleteId = ref(null)
const confirmClearHistory = ref(false)

const eventLocked = computed(() => Boolean(props.fixedEventType))
const hasFilters = computed(() => Boolean(deliveryWebhook.value || deliveryStatus.value || deliveryEvent.value))

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

async function loadDeliveries() {
  if (!opened.value) return
  loading.value = true
  error.value = ''
  try {
    deliveries.value = await listOutboundWebhookDeliveries({
      webhookId: deliveryWebhook.value,
      status: deliveryStatus.value,
      eventType: deliveryEvent.value,
      limit: 120,
    })
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.load')
  } finally {
    loading.value = false
  }
}

function handleToggle(event) {
  opened.value = event.currentTarget.open
  if (opened.value) loadDeliveries()
}

async function retryDelivery(row) {
  error.value = ''
  success.value = ''
  try {
    const result = await retryOutboundWebhookDelivery(row.id)
    success.value = result.status === 'success'
      ? t('admin.webhooks.messages.retrySuccess')
      : t('admin.webhooks.messages.retryFailed')
    await loadDeliveries()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.retry')
  }
}

async function deleteDelivery(row) {
  deleting.value = true
  error.value = ''
  success.value = ''
  try {
    await deleteOutboundWebhookDelivery(row.id)
    pendingDeliveryDeleteId.value = null
    success.value = t('admin.webhooks.deliveries.deleteSuccess')
    await loadDeliveries()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.deliveries.deleteError')
  } finally {
    deleting.value = false
  }
}

async function clearHistory() {
  deleting.value = true
  error.value = ''
  success.value = ''
  try {
    const result = await deleteOutboundWebhookDeliveryHistory({
      webhookId: deliveryWebhook.value,
      status: deliveryStatus.value,
      eventType: deliveryEvent.value,
    })
    confirmClearHistory.value = false
    success.value = t('admin.webhooks.deliveries.clearSuccess', { count: result.deleted_count })
    await loadDeliveries()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.deliveries.deleteError')
  } finally {
    deleting.value = false
  }
}

watch([deliveryWebhook, deliveryStatus, deliveryEvent], () => {
  pendingDeliveryDeleteId.value = null
  confirmClearHistory.value = false
  loadDeliveries()
})
</script>

<template>
  <details class="webhook-delivery-panel webhook-delivery-disclosure" @toggle="handleToggle">
    <summary class="webhook-delivery-summary">
      <span>
        <span class="command-deck-eyebrow">{{ t('admin.webhooks.deliveries.eyebrow') }}</span>
        <strong>{{ fixedEventType ? t('admin.webhooks.broadcast.historyTitle') : t('admin.webhooks.deliveries.title') }}</strong>
        <small>{{ t('admin.webhooks.deliveries.collapsedHint') }}</small>
      </span>
      <span class="summary-pill">{{ opened ? deliveries.length : t('admin.webhooks.deliveries.open') }}</span>
    </summary>

    <div class="webhook-delivery-body">
      <div class="webhook-section-head">
        <div>
          <h3>{{ fixedEventType ? t('admin.webhooks.broadcast.historyTitle') : t('admin.webhooks.deliveries.title') }}</h3>
          <p>{{ t('admin.webhooks.deliveries.manageHint') }}</p>
        </div>
        <div class="webhook-delivery-header-actions">
          <button class="small-action" type="button" :disabled="loading" @click="loadDeliveries">
            {{ t('admin.logs.refresh') }}
          </button>
          <button
            v-if="canManage && deliveries.length && !confirmClearHistory"
            class="danger-action"
            type="button"
            @click="confirmClearHistory = true"
          >
            {{ t('admin.webhooks.deliveries.clear') }}
          </button>
        </div>
      </div>

      <div v-if="confirmClearHistory" class="webhook-history-delete-confirmation" role="alert">
        <div>
          <strong>{{ t('admin.webhooks.deliveries.clearConfirmTitle') }}</strong>
          <span>{{ hasFilters ? t('admin.webhooks.deliveries.clearFilteredHint') : t('admin.webhooks.deliveries.clearAllHint') }}</span>
        </div>
        <div class="compact-actions">
          <button class="danger-action" type="button" :disabled="deleting" @click="clearHistory">
            {{ deleting ? t('admin.webhooks.deliveries.deleting') : t('admin.webhooks.deliveries.clearNow') }}
          </button>
          <button class="small-action" type="button" :disabled="deleting" @click="confirmClearHistory = false">
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>

      <p v-if="error" class="error-message">{{ error }}</p>
      <p v-if="success" class="success-message">{{ success }}</p>

      <div class="webhook-delivery-filters">
        <select v-model="deliveryWebhook">
          <option value="">{{ t('admin.webhooks.deliveries.allWebhooks') }}</option>
          <option v-for="row in webhooks" :key="row.id" :value="row.id">{{ row.name }}</option>
        </select>
        <select v-model="deliveryStatus">
          <option value="">{{ t('admin.webhooks.deliveries.allStatuses') }}</option>
          <option value="success">{{ t('admin.webhooks.status.success') }}</option>
          <option value="failed">{{ t('admin.webhooks.status.failed') }}</option>
          <option value="queued">{{ t('admin.webhooks.status.queued') }}</option>
          <option value="processing">{{ t('admin.webhooks.status.processing') }}</option>
        </select>
        <select v-if="!eventLocked" v-model="deliveryEvent">
          <option value="">{{ t('admin.workspace.filters.allWebhookEvents') }}</option>
          <option value="broadcast.manual">broadcast.manual</option>
          <option v-for="event in events" :key="event.key" :value="event.key">{{ event.key }}</option>
        </select>
      </div>

      <p v-if="loading" class="muted table-state">{{ t('admin.webhooks.loading') }}</p>
      <p v-else-if="deliveries.length === 0" class="muted table-state">{{ t('admin.webhooks.deliveries.empty') }}</p>
      <div v-else class="responsive-table-shell webhook-delivery-table-shell">
        <table class="security-table webhook-delivery-table">
          <thead>
            <tr>
              <th>{{ t('admin.webhooks.deliveries.created') }}</th>
              <th>{{ t('admin.webhooks.deliveries.webhook') }}</th>
              <th>{{ t('admin.webhooks.deliveries.event') }}</th>
              <th>{{ t('admin.webhooks.deliveries.status') }}</th>
              <th>HTTP</th>
              <th>{{ t('admin.webhooks.deliveries.details') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in deliveries" :key="row.id">
              <td>{{ formatDateTime(row.created_at) }}</td>
              <td>{{ row.webhook_name }}</td>
              <td><code>{{ row.event_type }}</code></td>
              <td><span class="webhook-delivery-status" :class="`is-${row.status}`">{{ t(`admin.webhooks.status.${row.status}`) }}</span></td>
              <td>{{ row.response_status || '—' }}</td>
              <td>{{ row.error_message || row.response_body || '—' }}</td>
              <td>
                <div v-if="pendingDeliveryDeleteId === row.id" class="webhook-delivery-row-confirmation">
                  <span>{{ t('admin.webhooks.deliveries.deleteConfirm') }}</span>
                  <button class="danger-action" type="button" :disabled="deleting" @click="deleteDelivery(row)">{{ t('common.delete') }}</button>
                  <button class="small-action" type="button" :disabled="deleting" @click="pendingDeliveryDeleteId = null">{{ t('common.cancel') }}</button>
                </div>
                <div v-else class="compact-actions">
                  <button v-if="canManage && row.status === 'failed'" class="small-action" type="button" @click="retryDelivery(row)">{{ t('admin.webhooks.actions.retry') }}</button>
                  <button v-if="canManage" class="danger-action" type="button" @click="pendingDeliveryDeleteId = row.id">{{ t('common.delete') }}</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </details>
</template>
