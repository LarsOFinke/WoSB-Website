<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import {
  createOutboundWebhook,
  deleteOutboundWebhook,
  getOutboundWebhookSummary,
  listOutboundWebhookDeliveries,
  listOutboundWebhookEvents,
  listOutboundWebhooks,
  retryOutboundWebhookDelivery,
  rotateOutboundWebhookSecret,
  testOutboundWebhook,
  updateOutboundWebhook,
} from '@/modules/admin/api/admin'

const props = defineProps({ canManage: { type: Boolean, default: false } })
const { locale, t } = useLocale()
const webhooks = ref([])
const events = ref([])
const deliveries = ref([])
const summary = ref({ total: 0, active: 0, failing: 0, discord: 0, signed_json: 0, successful_deliveries: 0, failed_deliveries: 0 })
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const revealedSecret = ref('')
const revealedSecretName = ref('')
const webhookSearch = ref('')
const webhookState = ref('')
const deliveryWebhook = ref('')
const deliveryStatus = ref('')
const deliveryEvent = ref('')

const form = reactive({
  id: null,
  name: '',
  endpoint_url: '',
  delivery_mode: 'discord',
  scope_type: 'global',
  scope_id: null,
  channel_key: '',
  message_template: '',
  discord_username: '',
  discord_avatar_url: '',
  is_active: true,
  event_types: [],
})

const groupedEvents = computed(() => {
  const groups = new Map()
  for (const event of events.value) {
    if (!groups.has(event.group)) groups.set(event.group, [])
    groups.get(event.group).push(event)
  }
  return [...groups.entries()].map(([key, items]) => ({ key, items }))
})
const filteredWebhooks = computed(() => {
  const term = webhookSearch.value.trim().toLowerCase()
  return webhooks.value.filter((row) => {
    const failing = Boolean(row.last_failure_at && (!row.last_success_at || new Date(row.last_failure_at) > new Date(row.last_success_at)))
    const searchText = `${row.name} ${row.endpoint_url} ${row.delivery_mode} ${row.scope_type} ${row.scope_id || ''} ${row.event_types.join(' ')}`.toLowerCase()
    if (term && !searchText.includes(term)) return false
    if (webhookState.value === 'active' && !row.is_active) return false
    if (webhookState.value === 'inactive' && row.is_active) return false
    if (webhookState.value === 'failing' && !failing) return false
    return true
  })
})

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
function resetForm() {
  Object.assign(form, { id: null, name: '', endpoint_url: '', delivery_mode: 'discord', scope_type: 'global', scope_id: null, channel_key: '', message_template: '', discord_username: '', discord_avatar_url: '', is_active: true, event_types: [] })
}
function editWebhook(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    endpoint_url: row.delivery_mode === 'discord' ? '' : row.endpoint_url,
    delivery_mode: row.delivery_mode,
    scope_type: row.scope_type,
    scope_id: row.scope_id,
    channel_key: row.channel_key || '',
    message_template: row.message_template || '',
    discord_username: row.discord_username || '',
    discord_avatar_url: row.discord_avatar_url || '',
    is_active: row.is_active,
    event_types: [...row.event_types],
  })
  requestAnimationFrame(() => document.querySelector('#outbound-webhook-name')?.focus())
}
function toggleEvent(eventType) {
  const selected = new Set(form.event_types)
  selected.has(eventType) ? selected.delete(eventType) : selected.add(eventType)
  form.event_types = [...selected]
}
async function loadDeliveries() {
  try {
    deliveries.value = await listOutboundWebhookDeliveries({ webhookId: deliveryWebhook.value, status: deliveryStatus.value, limit: 120 })
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.load')
  }
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const [hookRows, eventRows, totals] = await Promise.all([listOutboundWebhooks(), listOutboundWebhookEvents(), getOutboundWebhookSummary()])
    webhooks.value = hookRows
    events.value = eventRows
    summary.value = totals
    await loadDeliveries()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.load')
  } finally {
    loading.value = false
  }
}
async function submit() {
  saving.value = true
  error.value = ''
  success.value = ''
  revealedSecret.value = ''
  try {
    const payload = {
      name: form.name,
      endpoint_url: form.endpoint_url || null,
      delivery_mode: form.delivery_mode,
      scope_type: form.scope_type,
      scope_id: form.scope_type === 'global' ? null : Number(form.scope_id),
      channel_key: form.delivery_mode === 'signed_json' ? (form.channel_key || null) : null,
      message_template: form.message_template || null,
      discord_username: form.delivery_mode === 'discord' ? (form.discord_username || null) : null,
      discord_avatar_url: form.delivery_mode === 'discord' ? (form.discord_avatar_url || null) : null,
      is_active: form.is_active,
      event_types: form.event_types,
    }
    const result = form.id ? await updateOutboundWebhook(form.id, payload) : await createOutboundWebhook(payload)
    if (result.signing_secret) {
      revealedSecret.value = result.signing_secret
      revealedSecretName.value = result.name
    }
    success.value = form.id ? t('admin.webhooks.messages.updated') : t('admin.webhooks.messages.created')
    resetForm()
    await load()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.save')
  } finally {
    saving.value = false
  }
}
async function runTest(row) {
  try {
    const delivery = await testOutboundWebhook(row.id, row.event_types[0] || 'integration.test')
    success.value = delivery.status === 'success' ? t('admin.webhooks.messages.testSuccess') : t('admin.webhooks.messages.testFailed')
    await load()
  } catch (err) { error.value = err.message || t('admin.webhooks.errors.test') }
}
async function rotateSecret(row) {
  try {
    const result = await rotateOutboundWebhookSecret(row.id)
    revealedSecret.value = result.signing_secret || ''
    revealedSecretName.value = result.name
    success.value = t('admin.webhooks.messages.rotated')
    await load()
  } catch (err) { error.value = err.message || t('admin.webhooks.errors.rotate') }
}
async function removeWebhook(row) {
  if (!window.confirm(t('admin.webhooks.confirmDelete', { name: row.name }))) return
  try {
    await deleteOutboundWebhook(row.id)
    if (form.id === row.id) resetForm()
    success.value = t('admin.webhooks.messages.deleted')
    await load()
  } catch (err) { error.value = err.message || t('admin.webhooks.errors.delete') }
}
async function retryDelivery(row) {
  try {
    const result = await retryOutboundWebhookDelivery(row.id)
    success.value = result.status === 'success' ? t('admin.webhooks.messages.retrySuccess') : t('admin.webhooks.messages.retryFailed')
    await load()
  } catch (err) { error.value = err.message || t('admin.webhooks.errors.retry') }
}
async function copySecret() {
  if (!revealedSecret.value) return
  await navigator.clipboard.writeText(revealedSecret.value)
  success.value = t('admin.webhooks.messages.secretCopied')
}

watch([deliveryWebhook, deliveryStatus], loadDeliveries)
onMounted(load)
</script>

<template>
  <section class="outbound-webhook-management" :aria-label="t('admin.webhooks.title')">
    <div class="admin-panel-heading webhook-panel-heading">
      <div><span class="command-deck-eyebrow">{{ t('admin.webhooks.eyebrow') }}</span><h2>{{ t('admin.webhooks.title') }}</h2><p>{{ t('admin.webhooks.subtitle') }}</p></div>
      <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
    </div>

    <div class="webhook-summary-grid">
      <article><span>{{ t('admin.webhooks.summary.total') }}</span><strong>{{ summary.total }}</strong><small>{{ t('admin.webhooks.summary.totalHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.modes.discord') }}</span><strong>{{ summary.discord }}</strong><small>{{ t('admin.webhooks.summary.discordHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.modes.signed_json') }}</span><strong>{{ summary.signed_json }}</strong><small>{{ t('admin.webhooks.summary.signedHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.summary.deliveries') }}</span><strong>{{ summary.successful_deliveries }} / {{ summary.failed_deliveries }}</strong><small>{{ t('admin.webhooks.summary.deliveriesHint') }}</small></article>
    </div>

    <p v-if="error" class="error-text table-state">{{ error }}</p>
    <p v-if="success" class="success-text table-state">{{ success }}</p>
    <article v-if="revealedSecret" class="webhook-secret-reveal"><div><span class="command-deck-eyebrow">{{ t('admin.webhooks.secret.oneTime') }}</span><strong>{{ revealedSecretName }}</strong><code>{{ revealedSecret }}</code><small>{{ t('admin.webhooks.secret.hint') }}</small></div><button class="small-action primary-action" type="button" @click="copySecret">{{ t('admin.webhooks.secret.copy') }}</button></article>

    <div class="webhook-workspace-grid" :class="{ 'is-read-only': !canManage }">
      <form v-if="canManage" class="webhook-editor" @submit.prevent="submit">
        <div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('admin.webhooks.editor.eyebrow') }}</span><h3>{{ form.id ? t('admin.webhooks.editor.editTitle') : t('admin.webhooks.editor.createTitle') }}</h3></div><button v-if="form.id" class="small-action" type="button" @click="resetForm">{{ t('common.cancel') }}</button></div>
        <div class="webhook-editor-row">
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.mode') }}</span><select v-model="form.delivery_mode"><option value="discord">{{ t('admin.webhooks.modes.discord') }}</option><option value="signed_json">{{ t('admin.webhooks.modes.signed_json') }}</option></select></label>
          <label class="webhook-active-toggle"><input v-model="form.is_active" type="checkbox" /><span>{{ t('admin.webhooks.fields.active') }}</span></label>
        </div>
        <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.name') }}</span><input id="outbound-webhook-name" v-model="form.name" required maxlength="120" :placeholder="t('admin.webhooks.placeholders.name')" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.endpoint') }}</span><input v-model="form.endpoint_url" type="url" maxlength="1000" :required="!form.id || form.delivery_mode !== 'discord'" :placeholder="form.delivery_mode === 'discord' && form.id ? t('admin.webhooks.placeholders.keepEndpoint') : (form.delivery_mode === 'discord' ? 'https://discord.com/api/webhooks/…' : 'https://integration.example/hooks/rbf')" /></label>
        <div class="webhook-editor-row">
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.scope') }}</span><select v-model="form.scope_type"><option value="global">{{ t('admin.webhooks.scopes.global') }}</option><option value="fleet">{{ t('admin.webhooks.scopes.fleet') }}</option><option value="squad">{{ t('admin.webhooks.scopes.squad') }}</option></select></label>
          <label v-if="form.scope_type !== 'global'" class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.scopeId') }}</span><input v-model.number="form.scope_id" type="number" min="1" required /></label>
        </div>
        <div v-if="form.delivery_mode === 'discord'" class="webhook-editor-row">
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.discordUsername') }}</span><input v-model="form.discord_username" maxlength="80" /></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.discordAvatar') }}</span><input v-model="form.discord_avatar_url" type="url" maxlength="1000" /></label>
        </div>
        <label v-else class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.channelKey') }}</span><input v-model="form.channel_key" maxlength="120" :placeholder="t('admin.webhooks.placeholders.channelKey')" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.template') }}</span><textarea v-model="form.message_template" rows="4" maxlength="4000" :placeholder="t('admin.webhooks.placeholders.template')"></textarea><small>{{ t('admin.webhooks.templateHint') }}</small></label>
        <fieldset class="webhook-event-fieldset"><legend>{{ t('admin.webhooks.fields.events') }}</legend><p class="muted">{{ t('admin.webhooks.eventsHint') }}</p><div class="webhook-event-groups"><section v-for="group in groupedEvents" :key="group.key"><h4>{{ group.key }}</h4><label v-for="event in group.items" :key="event.key" class="webhook-event-option"><input :checked="form.event_types.includes(event.key)" type="checkbox" @change="toggleEvent(event.key)" /><span><strong>{{ event.key }}</strong><small>{{ event.description }}</small><code>{{ event.default_template }}</code></span></label></section></div></fieldset>
        <button class="form-button primary-action" type="submit" :disabled="saving || form.event_types.length === 0">{{ saving ? t('common.saving') : (form.id ? t('common.save') : t('admin.webhooks.actions.create')) }}</button>
      </form>

      <article v-else class="webhook-read-only-note"><span class="command-deck-eyebrow">{{ t('admin.webhooks.readOnly.eyebrow') }}</span><h3>{{ t('admin.webhooks.readOnly.title') }}</h3><p>{{ t('admin.webhooks.readOnly.hint') }}</p></article>

      <section class="webhook-list-panel">
        <div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('admin.webhooks.list.eyebrow') }}</span><h3>{{ t('admin.webhooks.list.title') }}</h3></div><span class="summary-pill">{{ filteredWebhooks.length }}</span></div>
        <div class="staff-filter-row"><label class="filter-box admin-search"><input v-model="webhookSearch" type="search" :placeholder="t('admin.workspace.filters.webhookSearch')" /></label><label class="filter-box select-shell"><select v-model="webhookState"><option value="">{{ t('admin.workspace.filters.allWebhookStates') }}</option><option value="active">{{ t('admin.webhooks.status.active') }}</option><option value="inactive">{{ t('admin.webhooks.status.inactive') }}</option><option value="failing">{{ t('admin.workspace.filters.failingWebhooks') }}</option></select></label></div>
        <p v-if="loading" class="muted table-state">{{ t('admin.webhooks.loading') }}</p><p v-else-if="filteredWebhooks.length === 0" class="muted table-state">{{ t('admin.webhooks.empty') }}</p>
        <div v-else class="webhook-card-list"><article v-for="row in filteredWebhooks" :key="row.id" class="webhook-card" :class="{ 'is-inactive': !row.is_active }"><div class="webhook-card-main"><div class="webhook-card-title"><strong>{{ row.name }}</strong><span class="webhook-status-pill" :class="{ 'is-active': row.is_active }">{{ row.is_active ? t('admin.webhooks.status.active') : t('admin.webhooks.status.inactive') }}</span></div><code>{{ row.endpoint_url }}</code><p><strong>{{ t(`admin.webhooks.modes.${row.delivery_mode}`) }}</strong> · {{ t(`admin.webhooks.scopes.${row.scope_type}`) }}<template v-if="row.scope_id"> #{{ row.scope_id }}</template> · {{ row.event_types.length }} {{ t('admin.webhooks.list.events') }}</p><div class="webhook-event-chip-row"><span v-for="eventType in row.event_types" :key="eventType">{{ eventType }}</span></div><small v-if="row.delivery_mode === 'signed_json'">{{ t('admin.webhooks.list.secret') }}: {{ row.secret_hint }}</small><small>{{ t('admin.webhooks.list.lastSuccess') }}: {{ formatDateTime(row.last_success_at) }} · {{ t('admin.webhooks.list.lastFailure') }}: {{ formatDateTime(row.last_failure_at) }}</small></div><div class="webhook-card-actions"><button class="small-action" type="button" @click="runTest(row)">{{ t('admin.webhooks.actions.test') }}</button><template v-if="canManage"><button class="small-action" type="button" @click="editWebhook(row)">{{ t('admin.webhooks.actions.edit') }}</button><button v-if="row.delivery_mode === 'signed_json'" class="small-action" type="button" @click="rotateSecret(row)">{{ t('admin.webhooks.actions.rotate') }}</button><button class="danger-action" type="button" @click="removeWebhook(row)">{{ t('common.delete') }}</button></template></div></article></div>
      </section>
    </div>

    <section class="webhook-delivery-panel"><div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('admin.webhooks.deliveries.eyebrow') }}</span><h3>{{ t('admin.webhooks.deliveries.title') }}</h3></div><div class="webhook-delivery-filters"><select v-model="deliveryWebhook"><option value="">{{ t('admin.webhooks.deliveries.allWebhooks') }}</option><option v-for="row in webhooks" :key="row.id" :value="row.id">{{ row.name }}</option></select><select v-model="deliveryStatus"><option value="">{{ t('admin.webhooks.deliveries.allStatuses') }}</option><option value="success">{{ t('admin.webhooks.status.success') }}</option><option value="failed">{{ t('admin.webhooks.status.failed') }}</option><option value="queued">{{ t('admin.webhooks.status.queued') }}</option></select><select v-model="deliveryEvent"><option value="">{{ t('admin.workspace.filters.allWebhookEvents') }}</option><option v-for="event in events" :key="event.key" :value="event.key">{{ event.key }}</option></select></div></div><p v-if="deliveries.filter(row => !deliveryEvent || row.event_type === deliveryEvent).length === 0" class="muted table-state">{{ t('admin.webhooks.deliveries.empty') }}</p><div v-else class="responsive-table-shell webhook-delivery-table-shell"><table class="security-table webhook-delivery-table"><thead><tr><th>{{ t('admin.webhooks.deliveries.created') }}</th><th>{{ t('admin.webhooks.deliveries.webhook') }}</th><th>{{ t('admin.webhooks.fields.mode') }}</th><th>{{ t('admin.webhooks.deliveries.event') }}</th><th>{{ t('admin.webhooks.deliveries.status') }}</th><th>HTTP</th><th>{{ t('admin.webhooks.deliveries.details') }}</th><th></th></tr></thead><tbody><tr v-for="row in deliveries.filter(item => !deliveryEvent || item.event_type === deliveryEvent)" :key="row.id"><td>{{ formatDateTime(row.created_at) }}</td><td>{{ row.webhook_name }}</td><td>{{ t(`admin.webhooks.modes.${row.delivery_mode}`) }}</td><td><code>{{ row.event_type }}</code></td><td><span class="webhook-delivery-status" :class="`is-${row.status}`">{{ t(`admin.webhooks.status.${row.status}`) }}</span></td><td>{{ row.response_status || '—' }}</td><td>{{ row.error_message || row.response_body || '—' }}</td><td><button v-if="canManage && row.status === 'failed'" class="small-action" type="button" @click="retryDelivery(row)">{{ t('admin.webhooks.actions.retry') }}</button></td></tr></tbody></table></div></section>
  </section>
</template>
