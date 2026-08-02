<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import WebhookDeliveryMonitor from '@/modules/admin/components/WebhookDeliveryMonitor.vue'
import {
  createOutboundWebhook,
  deleteOutboundWebhook,
  getOutboundWebhookSummary,
  listOutboundWebhookEvents,
  listOutboundWebhooks,
  testOutboundWebhook,
  updateOutboundWebhook,
} from '@/modules/admin/api/admin'
import {
  outboundWebhookPayload,
  webhookDraftIssues,
} from '@/modules/admin/domain/outboundWebhook'

const props = defineProps({ canManage: { type: Boolean, default: false } })
const { locale, t } = useLocale()
const webhooks = ref([])
const events = ref([])
const summary = ref({ total: 0, active: 0, failing: 0, successful_deliveries: 0, failed_deliveries: 0 })
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const webhookSearch = ref('')
const webhookState = ref('')
const eventSearch = ref('')
const templateEventKey = ref('')
const editorOpen = ref(false)
const validationIssues = ref([])
const channelPresets = [
  { key: 'moderation', label: '🔔 Moderation inbox', events: ['registration.request.created', 'fleet.application.created', 'privacy.request.created'] },
  { key: 'operations', label: '🛠️ Operations audit', events: ['system.update.started', 'system.update.result', 'system.maintenance.started', 'system.maintenance.ended', 'backup.run.requested', 'backup.restore.requested', 'backup.configuration.updated', 'backup.configuration.deleted', 'privacy.request.resolved'] },
  { key: 'calendar', label: '📣 Calendar shoutouts', events: ['calendar.event.created', 'calendar.event.updated', 'calendar.event.cancelled'] },
]

const form = reactive({
  id: null,
  name: '',
  endpoint_url: '',
  scope_type: 'global',
  scope_id: null,
  message_template: '',
  discord_username: '',
  broadcast_enabled: false,
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

const filteredEventGroups = computed(() => {
  const term = eventSearch.value.trim().toLowerCase()
  if (!term) return groupedEvents.value
  return groupedEvents.value
    .map((group) => ({
      ...group,
      items: group.items.filter((event) => `${event.key} ${event.description}`.toLowerCase().includes(term)),
    }))
    .filter((group) => group.items.length > 0)
})

const selectedEventsLabel = computed(() => form.event_types.length
  ? t('admin.webhooks.eventPicker.selected', { count: form.event_types.length })
  : t('admin.webhooks.eventPicker.none'))

const visibleSelectedEvents = computed(() => form.event_types.slice(0, 5))
const hiddenSelectedEventCount = computed(() => Math.max(0, form.event_types.length - visibleSelectedEvents.value.length))
const formIsReady = computed(() => webhookDraftIssues(form, { editing: Boolean(form.id) }).length === 0)

const filteredWebhooks = computed(() => {
  const term = webhookSearch.value.trim().toLowerCase()
  return webhooks.value.filter((row) => {
    const failing = Boolean(row.last_failure_at && (!row.last_success_at || new Date(row.last_failure_at) > new Date(row.last_success_at)))
    const searchText = `${row.name} ${row.endpoint_url} ${row.scope_type} ${row.scope_id || ''} ${row.event_types.join(' ')}`.toLowerCase()
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
  eventSearch.value = ''
  templateEventKey.value = ''
  validationIssues.value = []
  Object.assign(form, {
    id: null,
    name: '',
    endpoint_url: '',
    scope_type: 'global',
    scope_id: null,
    message_template: '',
    discord_username: '',
    broadcast_enabled: false,
    is_active: true,
    event_types: [],
  })
}

function openCreateWebhook() {
  resetForm()
  editorOpen.value = true
  requestAnimationFrame(() => document.querySelector('#outbound-webhook-name')?.focus())
}

function closeEditor() {
  editorOpen.value = false
  resetForm()
}

function editWebhook(row) {
  eventSearch.value = ''
  templateEventKey.value = ''
  Object.assign(form, {
    id: row.id,
    name: row.name,
    endpoint_url: '',
    scope_type: row.scope_type,
    scope_id: row.scope_id,
    message_template: row.message_template || '',
    discord_username: row.discord_username || '',
    broadcast_enabled: row.broadcast_enabled,
    is_active: row.is_active,
    event_types: [...row.event_types],
  })
  validationIssues.value = []
  editorOpen.value = true
  requestAnimationFrame(() => document.querySelector('#outbound-webhook-name')?.focus())
}

function toggleEvent(eventType) {
  const selected = new Set(form.event_types)
  selected.has(eventType) ? selected.delete(eventType) : selected.add(eventType)
  form.event_types = [...selected].sort()
}

function selectVisibleEvents() {
  const selected = new Set(form.event_types)
  for (const group of filteredEventGroups.value) {
    for (const event of group.items) selected.add(event.key)
  }
  form.event_types = [...selected].sort()
}

function clearEvents() {
  form.event_types = []
}

function applyChannelPreset(preset) {
  form.event_types = preset.events.filter((key) => events.value.some((event) => event.key === key))
  form.message_template = ''
  templateEventKey.value = ''
  if (!form.discord_username) form.discord_username = preset.label.replace(/^\S+\s/, '')
}

function applyTemplatePreset() {
  const selected = events.value.find((event) => event.key === templateEventKey.value)
  if (!selected) return
  form.message_template = selected.default_template
}

function clearMessageTemplate() {
  templateEventKey.value = ''
  form.message_template = ''
}


async function load() {
  loading.value = true
  error.value = ''
  try {
    const [hookRows, eventRows, totals] = await Promise.all([
      listOutboundWebhooks('automation'),
      listOutboundWebhookEvents(),
      getOutboundWebhookSummary('automation'),
    ])
    webhooks.value = hookRows
    events.value = eventRows
    summary.value = totals
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.load')
  } finally {
    loading.value = false
  }
}

async function submit() {
  validationIssues.value = webhookDraftIssues(form, { editing: Boolean(form.id) })
  if (validationIssues.value.length) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = outboundWebhookPayload(form)
    form.id ? await updateOutboundWebhook(form.id, payload) : await createOutboundWebhook(payload)
    success.value = form.id ? t('admin.webhooks.messages.updated') : t('admin.webhooks.messages.created')
    closeEditor()
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
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.test')
  }
}

async function removeWebhook(row) {
  if (!window.confirm(t('admin.webhooks.confirmDelete', { name: row.name }))) return
  try {
    await deleteOutboundWebhook(row.id)
    if (form.id === row.id) resetForm()
    success.value = t('admin.webhooks.messages.deleted')
    await load()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.errors.delete')
  }
}


watch(editorOpen, (isOpen) => {
  document.body.classList.toggle('webhook-editor-open', isOpen)
})
onBeforeUnmount(() => document.body.classList.remove('webhook-editor-open'))
onMounted(load)
</script>

<template>
  <section class="outbound-webhook-management" :aria-label="t('admin.webhooks.title')">
    <div class="admin-panel-heading webhook-panel-heading">
      <div>
        <span class="command-deck-eyebrow">{{ t('admin.webhooks.eyebrow') }}</span>
        <h2>{{ t('admin.webhooks.title') }}</h2>
        <p>{{ t('admin.webhooks.subtitle') }}</p>
      </div>
      <div class="hero-actions">
        <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
        <button v-if="canManage" class="form-button primary-action" type="button" @click="openCreateWebhook">{{ t('admin.webhooks.actions.create') }}</button>
      </div>
    </div>

    <div class="webhook-summary-grid">
      <article><span>{{ t('admin.webhooks.summary.total') }}</span><strong>{{ summary.total }}</strong><small>{{ t('admin.webhooks.summary.totalHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.summary.active') }}</span><strong>{{ summary.active }}</strong><small>{{ t('admin.webhooks.summary.activeHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.summary.failing') }}</span><strong>{{ summary.failing }}</strong><small>{{ t('admin.webhooks.summary.failingHint') }}</small></article>
      <article><span>{{ t('admin.webhooks.summary.deliveries') }}</span><strong>{{ summary.successful_deliveries }} / {{ summary.failed_deliveries }}</strong><small>{{ t('admin.webhooks.summary.deliveriesHint') }}</small></article>
    </div>

    <p v-if="error" class="error-message">{{ error }}</p>
    <p v-if="success" class="success-message">{{ success }}</p>

    <div class="webhook-workspace-grid" :class="{ 'is-read-only': !canManage, 'is-editing': editorOpen }">
      <article v-if="!canManage" class="webhook-read-only-note"><span class="command-deck-eyebrow">{{ t('admin.webhooks.readOnly.eyebrow') }}</span><h3>{{ t('admin.webhooks.readOnly.title') }}</h3><p>{{ t('admin.webhooks.readOnly.hint') }}</p></article>

      <section class="webhook-list-panel">
        <div class="webhook-section-head"><div><span class="command-deck-eyebrow">{{ t('admin.webhooks.list.eyebrow') }}</span><h3>{{ t('admin.webhooks.list.title') }}</h3></div><span class="summary-pill">{{ filteredWebhooks.length }}</span></div>
        <div class="staff-filter-row"><label class="filter-box admin-search"><input v-model="webhookSearch" type="search" :placeholder="t('admin.workspace.filters.webhookSearch')" /></label><label class="filter-box select-shell"><select v-model="webhookState"><option value="">{{ t('admin.workspace.filters.allWebhookStates') }}</option><option value="active">{{ t('admin.webhooks.status.active') }}</option><option value="inactive">{{ t('admin.webhooks.status.inactive') }}</option><option value="failing">{{ t('admin.workspace.filters.failingWebhooks') }}</option></select></label></div>
        <p v-if="loading" class="muted table-state">{{ t('admin.webhooks.loading') }}</p>
        <p v-else-if="filteredWebhooks.length === 0" class="muted table-state">{{ t('admin.webhooks.empty') }}</p>
        <div v-else class="webhook-card-list"><article v-for="row in filteredWebhooks" :key="row.id" class="webhook-card" :class="{ 'is-inactive': !row.is_active }"><div class="webhook-card-main"><div class="webhook-card-title"><strong>{{ row.name }}</strong><span class="webhook-status-pill" :class="{ 'is-active': row.is_active }">{{ row.is_active ? t('admin.webhooks.status.active') : t('admin.webhooks.status.inactive') }}</span></div><code>{{ row.endpoint_url }}</code><p>{{ t(`admin.webhooks.scopes.${row.scope_type}`) }}<template v-if="row.scope_id"> #{{ row.scope_id }}</template> · {{ row.event_types.length }} {{ t('admin.webhooks.list.events') }}<template v-if="row.broadcast_enabled"> · {{ t('admin.webhooks.list.broadcastTarget') }}</template></p><div class="webhook-event-chip-row"><span v-for="eventType in row.event_types.slice(0, 5)" :key="eventType">{{ eventType }}</span><span v-if="row.event_types.length > 5" class="webhook-event-more-chip">+{{ row.event_types.length - 5 }}</span></div><small>{{ t('admin.webhooks.list.lastSuccess') }}: {{ formatDateTime(row.last_success_at) }} · {{ t('admin.webhooks.list.lastFailure') }}: {{ formatDateTime(row.last_failure_at) }}</small></div><div class="webhook-card-actions"><button class="small-action" type="button" @click="runTest(row)">{{ t('admin.webhooks.actions.test') }}</button><template v-if="canManage"><button class="small-action" type="button" @click="editWebhook(row)">{{ t('admin.webhooks.actions.edit') }}</button><button class="danger-action" type="button" @click="removeWebhook(row)">{{ t('common.delete') }}</button></template></div></article></div>
      </section>
    </div>

    <Teleport to="body">
      <Transition name="webhook-editor">
        <div v-if="canManage && editorOpen" class="webhook-editor-layer" @keydown.esc="closeEditor">
          <button class="webhook-editor-backdrop" type="button" :aria-label="t('common.cancel')" @click="closeEditor"></button>
          <form class="webhook-editor" role="dialog" aria-modal="true" :aria-label="form.id ? t('admin.webhooks.editor.editTitle') : t('admin.webhooks.editor.createTitle')" @submit.prevent="submit">
          <div class="webhook-section-head">
          <div><span class="command-deck-eyebrow">{{ t('admin.webhooks.editor.eyebrow') }}</span><h3>{{ form.id ? t('admin.webhooks.editor.editTitle') : t('admin.webhooks.editor.createTitle') }}</h3></div>
          <button class="small-action" type="button" @click="closeEditor">{{ t('common.cancel') }}</button>
          </div>
          <div v-if="validationIssues.length" class="webhook-validation-summary" role="alert">
          <strong>{{ t('admin.webhooks.validation.title') }}</strong>
          <ul><li v-for="issue in validationIssues" :key="issue">{{ t(`admin.webhooks.validation.${issue}`) }}</li></ul>
          </div>
          <div class="webhook-toggle-row"><label class="webhook-active-toggle"><input v-model="form.is_active" type="checkbox" /><span>{{ t('admin.webhooks.fields.active') }}</span></label></div>
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.name') }}</span><input id="outbound-webhook-name" v-model="form.name" required minlength="3" maxlength="120" :placeholder="t('admin.webhooks.placeholders.name')" /></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.endpoint') }}</span><input v-model="form.endpoint_url" type="text" inputmode="url" autocapitalize="none" :spellcheck="false" maxlength="1000" :required="!form.id" :placeholder="form.id ? t('admin.webhooks.placeholders.keepEndpoint') : 'https://discord.com/api/webhooks/…'" /><small>{{ t('admin.webhooks.endpointHint') }}</small></label>
          <div class="webhook-editor-row">
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.scope') }}</span><select v-model="form.scope_type"><option value="global">{{ t('admin.webhooks.scopes.global') }}</option><option value="fleet">{{ t('admin.webhooks.scopes.fleet') }}</option><option value="squad">{{ t('admin.webhooks.scopes.squad') }}</option></select></label>
          <label v-if="form.scope_type !== 'global'" class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.scopeId') }}</span><input v-model.number="form.scope_id" type="number" min="1" required /></label>
          </div>
          <div class="webhook-editor-row">
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.discordUsername') }}</span><input v-model="form.discord_username" maxlength="80" /></label>
          </div>
          <section class="webhook-template-composer" :aria-label="t('admin.webhooks.fields.template')">
          <label class="input-panel embedded-field webhook-template-picker">
          <span>{{ t('admin.webhooks.templatePicker.label') }}</span>
          <div class="webhook-template-picker-row">
          <select v-model="templateEventKey">
          <option value="">{{ t('admin.webhooks.templatePicker.placeholder') }}</option>
          <optgroup v-for="group in groupedEvents" :key="group.key" :label="group.key">
          <option v-for="event in group.items" :key="event.key" :value="event.key">{{ event.key }} · {{ event.description }}</option>
          </optgroup>
          </select>
          <button class="small-action" type="button" :disabled="!templateEventKey" @click="applyTemplatePreset">{{ t('admin.webhooks.templatePicker.apply') }}</button>
          <button v-if="form.message_template" class="small-action" type="button" @click="clearMessageTemplate">{{ t('admin.webhooks.templatePicker.useDefaults') }}</button>
          </div>
          <small>{{ t('admin.webhooks.templatePicker.hint') }}</small>
          </label>
          <label class="input-panel embedded-field">
          <span>{{ t('admin.webhooks.fields.template') }}</span>
          <textarea v-model="form.message_template" rows="6" maxlength="4000" :placeholder="t('admin.webhooks.placeholders.template')"></textarea>
          <small>{{ t('admin.webhooks.templateHint') }}</small>
          </label>
          </section>
          <fieldset class="webhook-event-fieldset">
          <legend>{{ t('admin.webhooks.fields.events') }}</legend>
          <p class="muted">{{ t('admin.webhooks.eventsHint') }}</p>
          <div class="webhook-channel-presets" aria-label="Recommended Discord channel presets">
          <button v-for="preset in channelPresets" :key="preset.key" class="small-action" type="button" @click="applyChannelPreset(preset)">{{ preset.label }}</button>
          </div>
          <details class="webhook-event-dropdown">
          <summary>
          <span><strong>{{ selectedEventsLabel }}</strong><small>{{ t('admin.webhooks.eventPicker.summaryHint') }}</small></span>
          <span class="summary-pill">{{ form.event_types.length }}</span>
          </summary>
          <div class="webhook-event-dropdown-panel">
          <div class="webhook-event-dropdown-toolbar">
          <label class="filter-box admin-search"><input v-model="eventSearch" type="search" :placeholder="t('admin.webhooks.eventPicker.search')" /></label>
          <div class="webhook-event-dropdown-actions">
          <button class="small-action" type="button" :disabled="filteredEventGroups.length === 0" @click="selectVisibleEvents">{{ t('admin.webhooks.eventPicker.selectVisible') }}</button>
          <button class="small-action" type="button" :disabled="form.event_types.length === 0" @click="clearEvents">{{ t('admin.webhooks.eventPicker.clear') }}</button>
          </div>
          </div>
          <div v-if="filteredEventGroups.length" class="webhook-event-groups">
          <section v-for="group in filteredEventGroups" :key="group.key">
          <h4>{{ group.key }}</h4>
          <label v-for="event in group.items" :key="event.key" class="webhook-event-option">
          <input :checked="form.event_types.includes(event.key)" type="checkbox" @change="toggleEvent(event.key)" />
          <span><strong>{{ event.key }}</strong><small>{{ event.description }}</small></span>
          </label>
          </section>
          </div>
          <p v-else class="muted table-state">{{ t('admin.webhooks.eventPicker.empty') }}</p>
          </div>
          </details>
          <div v-if="form.event_types.length" class="webhook-event-chip-row is-selection">
          <button v-for="eventType in visibleSelectedEvents" :key="eventType" type="button" :aria-label="t('admin.webhooks.eventPicker.remove', { event: eventType })" @click="toggleEvent(eventType)"><span>{{ eventType }}</span><b aria-hidden="true">×</b></button><span v-if="hiddenSelectedEventCount" class="webhook-event-more-chip">+{{ hiddenSelectedEventCount }}</span>
          </div>
          </fieldset>
          <div class="webhook-editor-actions"><button class="small-action" type="button" @click="closeEditor">{{ t('common.cancel') }}</button><button class="form-button primary-action" type="submit" :disabled="saving || !formIsReady">{{ saving ? t('common.saving') : (form.id ? t('common.save') : t('admin.webhooks.actions.create')) }}</button></div>
          </form>
        </div>
      </Transition>
    </Teleport>

    <WebhookDeliveryMonitor :webhooks="webhooks" :events="events" :can-manage="canManage" />
  </section>
</template>
