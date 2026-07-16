<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import {
  listBroadcastWebhookTargets,
  sendDiscordBroadcast,
} from '@/modules/admin/api/admin'

const props = defineProps({ canManage: { type: Boolean, default: false } })
const { t } = useLocale()
const targets = ref([])
const loading = ref(false)
const sending = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({
  webhook_ids: [],
  message: '',
  discord_username: '',
  discord_avatar_url: '',
})

const allSelected = computed(
  () => targets.value.length > 0 && form.webhook_ids.length === targets.value.length,
)
const selectedTargets = computed(() =>
  targets.value.filter((target) => form.webhook_ids.includes(target.id)),
)

function toggleTarget(id) {
  const selected = new Set(form.webhook_ids)
  selected.has(id) ? selected.delete(id) : selected.add(id)
  form.webhook_ids = [...selected]
}

function toggleAll() {
  form.webhook_ids = allSelected.value ? [] : targets.value.map((target) => target.id)
}

async function loadTargets() {
  if (!props.canManage) return
  loading.value = true
  error.value = ''
  try {
    const rows = await listBroadcastWebhookTargets()
    targets.value = rows
    const available = new Set(rows.map((row) => row.id))
    form.webhook_ids = form.webhook_ids.filter((id) => available.has(id))
  } catch (err) {
    error.value = err.message || t('admin.webhooks.broadcast.errors.load')
  } finally {
    loading.value = false
  }
}

async function submit() {
  sending.value = true
  error.value = ''
  success.value = ''
  try {
    const rows = await sendDiscordBroadcast({
      webhook_ids: form.webhook_ids,
      message: form.message,
      discord_username: form.discord_username || null,
      discord_avatar_url: form.discord_avatar_url || null,
    })
    success.value = t('admin.webhooks.broadcast.messages.queued', { count: rows.length })
    form.message = ''
  } catch (err) {
    error.value = err.message || t('admin.webhooks.broadcast.errors.send')
  } finally {
    sending.value = false
  }
}

onMounted(loadTargets)
</script>

<template>
  <section v-if="canManage" class="discord-broadcast-panel wire-section" :aria-label="t('admin.webhooks.broadcast.title')">
    <div class="webhook-panel-heading">
      <div>
        <span class="command-deck-eyebrow">{{ t('admin.webhooks.broadcast.eyebrow') }}</span>
        <h2>{{ t('admin.webhooks.broadcast.title') }}</h2>
        <p>{{ t('admin.webhooks.broadcast.subtitle') }}</p>
      </div>
      <button class="small-action" type="button" :disabled="loading" @click="loadTargets">
        {{ t('admin.logs.refresh') }}
      </button>
    </div>

    <p v-if="error" class="error-message">{{ error }}</p>
    <p v-if="success" class="success-message">{{ success }}</p>

    <form class="broadcast-compose-grid" @submit.prevent="submit">
      <section class="broadcast-target-panel">
        <div class="webhook-section-head">
          <div>
            <span class="command-deck-eyebrow">{{ t('admin.webhooks.broadcast.targets.eyebrow') }}</span>
            <h3>{{ t('admin.webhooks.broadcast.targets.title') }}</h3>
          </div>
          <button v-if="targets.length" class="small-action" type="button" @click="toggleAll">
            {{ allSelected ? t('admin.webhooks.broadcast.targets.clearAll') : t('admin.webhooks.broadcast.targets.selectAll') }}
          </button>
        </div>
        <p v-if="loading" class="muted">{{ t('admin.webhooks.loading') }}</p>
        <p v-else-if="targets.length === 0" class="muted">
          {{ t('admin.webhooks.broadcast.targets.empty') }}
        </p>
        <div v-else class="broadcast-target-list">
          <label v-for="target in targets" :key="target.id" class="broadcast-target-option">
            <input
              :checked="form.webhook_ids.includes(target.id)"
              type="checkbox"
              @change="toggleTarget(target.id)"
            />
            <span>
              <strong>{{ target.name }}</strong>
              <code>{{ target.endpoint_url }}</code>
            </span>
          </label>
        </div>
      </section>

      <section class="broadcast-message-panel">
        <div class="webhook-section-head">
          <div>
            <span class="command-deck-eyebrow">{{ t('admin.webhooks.broadcast.message.eyebrow') }}</span>
            <h3>{{ t('admin.webhooks.broadcast.message.title') }}</h3>
          </div>
          <span class="summary-pill">{{ form.message.length }} / 2000</span>
        </div>
        <label class="input-panel embedded-field">
          <span>{{ t('admin.webhooks.broadcast.fields.message') }}</span>
          <textarea
            v-model="form.message"
            rows="8"
            maxlength="2000"
            required
            :placeholder="t('admin.webhooks.broadcast.placeholders.message')"
          ></textarea>
          <small>{{ t('admin.webhooks.broadcast.messageHint') }}</small>
        </label>
        <div class="webhook-editor-row">
          <label class="input-panel embedded-field">
            <span>{{ t('admin.webhooks.fields.discordUsername') }}</span>
            <input v-model="form.discord_username" maxlength="80" />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.webhooks.fields.discordAvatar') }}</span>
            <input v-model="form.discord_avatar_url" type="url" maxlength="1000" />
          </label>
        </div>
        <p class="muted broadcast-selection-summary">
          {{ t('admin.webhooks.broadcast.selected', { count: selectedTargets.length }) }}
        </p>
        <button
          class="form-button primary-action"
          type="submit"
          :disabled="sending || form.webhook_ids.length === 0 || !form.message.trim()"
        >
          {{ sending ? t('admin.webhooks.broadcast.actions.sending') : t('admin.webhooks.broadcast.actions.send') }}
        </button>
      </section>
    </form>
  </section>
</template>
