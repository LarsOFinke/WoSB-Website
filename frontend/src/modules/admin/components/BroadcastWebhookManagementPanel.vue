<script setup>
import { computed, reactive, ref, onMounted } from 'vue'

import { useLocale } from '@/locales'
import {
  createOutboundWebhook,
  deleteOutboundWebhook,
  listOutboundWebhooks,
  updateOutboundWebhook,
} from '@/modules/admin/api/admin'

const props = defineProps({ canManage: { type: Boolean, default: false } })
const emit = defineEmits(['changed'])
const { t } = useLocale()
const webhooks = ref([])
const loading = ref(false)
const saving = ref(false)
const editorOpen = ref(false)
const error = ref('')
const success = ref('')
const sourceRow = ref(null)
const form = reactive({
  id: null,
  name: '',
  endpoint_url: '',
  discord_username: '',
  discord_avatar_url: '',
  is_active: true,
})

const broadcastWebhooks = computed(() => webhooks.value.filter((row) => row.broadcast_enabled))

function resetForm() {
  sourceRow.value = null
  Object.assign(form, {
    id: null,
    name: '',
    endpoint_url: '',
    discord_username: '',
    discord_avatar_url: '',
    is_active: true,
  })
}

function openCreate() {
  resetForm()
  editorOpen.value = true
}

function editTarget(row) {
  sourceRow.value = row
  Object.assign(form, {
    id: row.id,
    name: row.name,
    endpoint_url: '',
    discord_username: row.discord_username || '',
    discord_avatar_url: row.discord_avatar_url || '',
    is_active: row.is_active,
  })
  editorOpen.value = true
}

function closeEditor() {
  editorOpen.value = false
  resetForm()
}

async function load() {
  if (!props.canManage) return
  loading.value = true
  error.value = ''
  try {
    webhooks.value = await listOutboundWebhooks('broadcast')
    emit('changed', broadcastWebhooks.value)
  } catch (err) {
    error.value = err.message || t('admin.webhooks.broadcast.targets.loadError')
  } finally {
    loading.value = false
  }
}

function payload() {
  const existing = sourceRow.value
  return {
    name: form.name,
    endpoint_url: form.endpoint_url || null,
    event_types: existing?.event_types || [],
    scope_type: existing?.scope_type || 'global',
    scope_id: existing?.scope_id || null,
    message_template: existing?.message_template || null,
    discord_username: form.discord_username || null,
    discord_avatar_url: form.discord_avatar_url || null,
    broadcast_enabled: true,
    is_active: form.is_active,
  }
}

async function submit() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    if (form.id) await updateOutboundWebhook(form.id, payload())
    else await createOutboundWebhook({ ...payload(), endpoint_url: form.endpoint_url })
    success.value = form.id
      ? t('admin.webhooks.broadcast.targets.updated')
      : t('admin.webhooks.broadcast.targets.created')
    closeEditor()
    await load()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.broadcast.targets.saveError')
  } finally {
    saving.value = false
  }
}

async function removeTarget(row) {
  const sharedWithAutomation = row.event_types.length > 0
  const confirmationKey = sharedWithAutomation
    ? 'admin.webhooks.broadcast.targets.confirmDetach'
    : 'admin.webhooks.broadcast.targets.confirmDelete'
  if (!window.confirm(t(confirmationKey, { name: row.name, count: row.event_types.length }))) return
  error.value = ''
  success.value = ''
  try {
    if (sharedWithAutomation) {
      await updateOutboundWebhook(row.id, {
        name: row.name,
        endpoint_url: null,
        event_types: row.event_types,
        scope_type: row.scope_type,
        scope_id: row.scope_id,
        message_template: row.message_template,
        discord_username: row.discord_username,
        discord_avatar_url: row.discord_avatar_url,
        broadcast_enabled: false,
        is_active: row.is_active,
      })
      success.value = t('admin.webhooks.broadcast.targets.detached')
    } else {
      await deleteOutboundWebhook(row.id)
      success.value = t('admin.webhooks.broadcast.targets.deleted')
    }
    await load()
  } catch (err) {
    error.value = err.message || t('admin.webhooks.broadcast.targets.deleteError')
  }
}

onMounted(load)

defineExpose({ load, broadcastWebhooks })
</script>

<template>
  <section v-if="canManage" class="broadcast-webhook-management wire-section">
    <div class="webhook-panel-heading">
      <div>
        <span class="command-deck-eyebrow">{{ t('admin.webhooks.broadcast.managementEyebrow') }}</span>
        <h2>{{ t('admin.webhooks.broadcast.managementTitle') }}</h2>
        <p>{{ t('admin.webhooks.broadcast.managementSubtitle') }}</p>
      </div>
      <div class="hero-actions">
        <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
        <button class="form-button primary-action" type="button" @click="openCreate">{{ t('admin.webhooks.broadcast.targets.create') }}</button>
      </div>
    </div>

    <p v-if="error" class="error-message">{{ error }}</p>
    <p v-if="success" class="success-message">{{ success }}</p>

    <p v-if="loading" class="muted table-state">{{ t('admin.webhooks.loading') }}</p>
    <p v-else-if="broadcastWebhooks.length === 0" class="muted table-state">{{ t('admin.webhooks.broadcast.targets.emptyManaged') }}</p>
    <div v-else class="webhook-card-list broadcast-target-management-list">
      <article v-for="row in broadcastWebhooks" :key="row.id" class="webhook-card" :class="{ 'is-inactive': !row.is_active }">
        <div class="webhook-card-main">
          <div class="webhook-card-title">
            <strong>{{ row.name }}</strong>
            <span class="webhook-status-pill" :class="{ 'is-active': row.is_active }">{{ row.is_active ? t('admin.webhooks.status.active') : t('admin.webhooks.status.inactive') }}</span>
          </div>
          <code>{{ row.endpoint_url }}</code>
          <p>{{ t('admin.webhooks.broadcast.targets.externalHint') }}</p>
          <small v-if="row.event_types.length">{{ t('admin.webhooks.broadcast.targets.sharedAutomation', { count: row.event_types.length }) }}</small>
        </div>
        <div class="webhook-card-actions">
          <button class="small-action" type="button" @click="editTarget(row)">{{ t('admin.webhooks.actions.edit') }}</button>
          <button class="danger-action" type="button" @click="removeTarget(row)">{{ t('common.delete') }}</button>
        </div>
      </article>
    </div>

    <Teleport to="body">
      <div v-if="editorOpen" class="webhook-editor-layer" @keydown.esc="closeEditor">
        <button class="webhook-editor-backdrop" type="button" :aria-label="t('common.cancel')" @click="closeEditor"></button>
        <form class="webhook-editor broadcast-target-editor" role="dialog" aria-modal="true" :aria-label="form.id ? t('admin.webhooks.broadcast.targets.editTitle') : t('admin.webhooks.broadcast.targets.createTitle')" @submit.prevent="submit">
          <div class="webhook-section-head">
            <div>
              <span class="command-deck-eyebrow">{{ t('admin.webhooks.broadcast.targets.eyebrow') }}</span>
              <h3>{{ form.id ? t('admin.webhooks.broadcast.targets.editTitle') : t('admin.webhooks.broadcast.targets.createTitle') }}</h3>
            </div>
            <button class="small-action" type="button" @click="closeEditor">{{ t('common.cancel') }}</button>
          </div>
          <label class="webhook-active-toggle"><input v-model="form.is_active" type="checkbox" /><span>{{ t('admin.webhooks.fields.active') }}</span></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.name') }}</span><input v-model="form.name" required minlength="3" maxlength="120" :placeholder="t('admin.webhooks.broadcast.targets.namePlaceholder')" /></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.endpoint') }}</span><input v-model="form.endpoint_url" type="text" inputmode="url" autocapitalize="none" :spellcheck="false" maxlength="1000" :required="!form.id" :placeholder="form.id ? t('admin.webhooks.placeholders.keepEndpoint') : 'https://discord.com/api/webhooks/…'" /><small>{{ t('admin.webhooks.endpointHint') }}</small></label>
          <div class="webhook-editor-row">
            <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.discordUsername') }}</span><input v-model="form.discord_username" maxlength="80" /></label>
            <label class="input-panel embedded-field"><span>{{ t('admin.webhooks.fields.discordAvatar') }}</span><input v-model="form.discord_avatar_url" type="url" maxlength="1000" /></label>
          </div>
          <p class="muted">{{ t('admin.webhooks.broadcast.targets.separationHint') }}</p>
          <div class="webhook-editor-actions"><button class="small-action" type="button" @click="closeEditor">{{ t('common.cancel') }}</button><button class="form-button primary-action" type="submit" :disabled="saving || form.name.trim().length < 3 || (!form.id && !form.endpoint_url.trim())">{{ saving ? t('common.saving') : t('common.save') }}</button></div>
        </form>
      </div>
    </Teleport>
  </section>
</template>
