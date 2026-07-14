<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { configureDiscordBot, getDiscordBotStatus, requestDiscordBotOperation } from '@/modules/admin/api/admin'

const { locale, t } = useLocale()
const bot = ref({
  state: 'idle',
  operation: 'status',
  message: '',
  configured: false,
  installed: false,
  service_state: 'unknown',
  version: null,
  commit: null,
  log_tail: [],
  request_available: false,
  configuration: {},
})
const loading = ref(false)
const configurationSaving = ref(false)
const configurationInitialized = ref(false)
const error = ref('')
const success = ref('')
let pollTimer = null

const configurationForm = reactive({
  discord_bot_token: '',
  webhook_secret: '',
  website_base_url: '',
  events_channel_id: '',
  guides_channel_id: '',
  builds_channel_id: '',
  forum_channel_id: '',
  default_channel_id: '',
  suppress_notifications: false,
  timestamp_tolerance_seconds: 300,
  request_timeout_seconds: 15,
  max_attempts: 3,
  restart_after_save: true,
})

const inProgress = computed(() => ['queued', 'running'].includes(bot.value.state))
const stateLabel = computed(() => t(`admin.system.states.${bot.value.state || 'idle'}`))
const serviceLabel = computed(() => t(`admin.system.discordBot.serviceStates.${bot.value.service_state || 'unknown'}`))
const config = computed(() => bot.value.configuration || {})
const webhookEndpoint = computed(() => {
  const base = String(configurationForm.website_base_url || config.value.website_base_url || '').replace(/\/$/, '')
  return base ? `${base}/integrations/discord/webhooks/rbf` : '—'
})
const canSaveConfiguration = computed(() => {
  if (!bot.value.installed || inProgress.value || configurationSaving.value || !bot.value.request_available) return false
  if (!configurationForm.website_base_url.trim()) return false
  const channels = [
    configurationForm.events_channel_id,
    configurationForm.guides_channel_id,
    configurationForm.builds_channel_id,
    configurationForm.forum_channel_id,
    configurationForm.default_channel_id,
  ]
  if (channels.some((value) => !/^\d{15,22}$/.test(String(value || '').trim()))) return false
  if (!config.value.discord_token_configured && configurationForm.discord_bot_token.trim().length < 20) return false
  if (!config.value.webhook_secret_configured && configurationForm.webhook_secret.trim().length < 32) return false
  return true
})

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function applyConfigurationStatus() {
  if (configurationInitialized.value) return
  const current = bot.value.configuration || {}
  const channels = current.channels || {}
  configurationForm.website_base_url = current.website_base_url || (typeof window !== 'undefined' ? window.location.origin : '')
  configurationForm.events_channel_id = channels.events || ''
  configurationForm.guides_channel_id = channels.guides || ''
  configurationForm.builds_channel_id = channels.builds || ''
  configurationForm.forum_channel_id = channels.forum || ''
  configurationForm.default_channel_id = channels.default || ''
  configurationForm.suppress_notifications = Boolean(current.suppress_notifications)
  configurationForm.timestamp_tolerance_seconds = Number(current.timestamp_tolerance_seconds || 300)
  configurationForm.request_timeout_seconds = Number(current.request_timeout_seconds || 15)
  configurationForm.max_attempts = Number(current.max_attempts || 3)
  configurationInitialized.value = true
}

function schedulePoll() {
  window.clearTimeout(pollTimer)
  if (!inProgress.value) return
  pollTimer = window.setTimeout(async () => {
    await loadStatus({ preserveConfigurationForm: true })
    schedulePoll()
  }, 3000)
}

async function loadStatus({ preserveConfigurationForm = false } = {}) {
  loading.value = true
  error.value = ''
  try {
    bot.value = await getDiscordBotStatus()
    if (!preserveConfigurationForm) configurationInitialized.value = false
    applyConfigurationStatus()
  } catch (err) {
    error.value = err.message || t('admin.system.discordBot.loadError')
  } finally {
    loading.value = false
  }
}

async function trigger(operation) {
  if (inProgress.value || !bot.value.request_available) return
  if (['install', 'stop'].includes(operation) && !window.confirm(t(`admin.system.discordBot.confirm.${operation}`))) return
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await requestDiscordBotOperation(operation)
    bot.value = response.status
    success.value = t('admin.system.discordBot.requestAccepted', { operation: t(`admin.system.discordBot.operations.${operation}`) })
    schedulePoll()
  } catch (err) {
    error.value = err.message || t('admin.system.discordBot.requestError')
  } finally {
    loading.value = false
  }
}

async function saveConfiguration() {
  if (!canSaveConfiguration.value) return
  configurationSaving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = {
      website_base_url: configurationForm.website_base_url.trim().replace(/\/$/, ''),
      channels: {
        events: configurationForm.events_channel_id.trim(),
        guides: configurationForm.guides_channel_id.trim(),
        builds: configurationForm.builds_channel_id.trim(),
        forum: configurationForm.forum_channel_id.trim(),
        default: configurationForm.default_channel_id.trim(),
      },
      suppress_notifications: configurationForm.suppress_notifications,
      timestamp_tolerance_seconds: Number(configurationForm.timestamp_tolerance_seconds),
      request_timeout_seconds: Number(configurationForm.request_timeout_seconds),
      max_attempts: Number(configurationForm.max_attempts),
      restart_after_save: configurationForm.restart_after_save,
    }
    if (configurationForm.discord_bot_token.trim()) payload.discord_bot_token = configurationForm.discord_bot_token.trim()
    if (configurationForm.webhook_secret.trim()) payload.webhook_secret = configurationForm.webhook_secret.trim()
    const response = await configureDiscordBot(payload)
    bot.value = response.status
    configurationForm.discord_bot_token = ''
    configurationForm.webhook_secret = ''
    success.value = t('admin.system.discordBot.configuration.requestAccepted')
    schedulePoll()
  } catch (err) {
    error.value = err.message || t('admin.system.discordBot.configuration.saveError')
  } finally {
    configurationSaving.value = false
  }
}

onMounted(async () => {
  await loadStatus()
  schedulePoll()
})
onUnmounted(() => window.clearTimeout(pollTimer))
</script>

<template>
  <section class="discord-bot-operations" aria-live="polite">
    <div class="admin-panel-heading compact-heading">
      <div>
        <span class="command-deck-eyebrow">{{ t('admin.system.discordBot.eyebrow') }}</span>
        <h3>{{ t('admin.system.discordBot.title') }}</h3>
        <p>{{ t('admin.system.discordBot.subtitle') }}</p>
      </div>
      <button class="small-action" type="button" :disabled="loading" @click="trigger('refresh')">{{ t('admin.system.refresh') }}</button>
    </div>

    <div class="discord-bot-setup-flow">
      <article class="discord-bot-setup-step" :class="{ 'is-ready': bot.configured }">
        <span>01</span>
        <div>
          <strong>{{ t('admin.system.discordBot.setup.repositoryTitle') }}</strong>
          <p>{{ t('admin.system.discordBot.setup.repositoryText') }}</p>
          <code>/etc/rbf-hub/discord-bot-manager.env</code>
        </div>
      </article>
      <article class="discord-bot-setup-step" :class="{ 'is-ready': bot.installed }">
        <span>02</span>
        <div>
          <strong>{{ t('admin.system.discordBot.setup.installTitle') }}</strong>
          <p>{{ t('admin.system.discordBot.setup.installText') }}</p>
        </div>
      </article>
      <article class="discord-bot-setup-step" :class="{ 'is-ready': config.ready }">
        <span>03</span>
        <div>
          <strong>{{ t('admin.system.discordBot.setup.configurationTitle') }}</strong>
          <p>{{ t('admin.system.discordBot.setup.configurationText') }}</p>
        </div>
      </article>
    </div>

    <div class="discord-bot-status-grid">
      <article class="home-status-card refined-status-card discord-bot-status-card">
        <span>{{ t('admin.system.discordBot.managerState') }}</span>
        <strong>{{ stateLabel }}</strong>
        <p>{{ bot.message || t('admin.system.discordBot.notConfigured') }}</p>
        <div class="discord-bot-badge-row">
          <span class="summary-pill" :class="{ 'is-ready': bot.configured }">{{ bot.configured ? t('admin.system.discordBot.configured') : t('admin.system.discordBot.configurationMissing') }}</span>
          <span class="summary-pill" :class="{ 'is-ready': bot.installed }">{{ bot.installed ? t('admin.system.discordBot.installed') : t('admin.system.discordBot.notInstalled') }}</span>
          <span class="summary-pill" :class="{ 'is-ready': config.ready }">{{ config.ready ? t('admin.system.discordBot.configuration.ready') : t('admin.system.discordBot.configuration.pending') }}</span>
          <span class="summary-pill" :class="{ 'is-ready': bot.service_state === 'active' }">{{ serviceLabel }}</span>
        </div>
      </article>

      <article class="home-status-card refined-status-card discord-bot-detail-card">
        <span>{{ t('admin.system.discordBot.runtime') }}</span>
        <dl class="system-update-meta">
          <div><dt>{{ t('admin.system.discordBot.version') }}</dt><dd>{{ bot.version || '—' }}</dd></div>
          <div><dt>{{ t('admin.system.discordBot.gatewayBinding') }}</dt><dd><code>{{ config.bind_host || '0.0.0.0' }}:{{ config.listen_port || 8765 }}</code></dd></div>
          <div><dt>{{ t('admin.system.discordBot.firewallMode') }}</dt><dd>{{ config.firewall_mode || 'auto' }}</dd></div>
          <div><dt>{{ t('admin.system.commit') }}</dt><dd>{{ bot.commit || '—' }}</dd></div>
          <div><dt>{{ t('admin.system.requestedBy') }}</dt><dd>{{ bot.requested_by || '—' }}</dd></div>
          <div><dt>{{ t('admin.system.startedAt') }}</dt><dd>{{ formatDateTime(bot.started_at) }}</dd></div>
          <div><dt>{{ t('admin.system.finishedAt') }}</dt><dd>{{ formatDateTime(bot.finished_at) }}</dd></div>
        </dl>
      </article>
    </div>

    <div class="discord-bot-action-grid">
      <button v-if="!bot.installed" class="form-button primary-action" type="button" :disabled="loading || inProgress || !bot.request_available || !bot.configured" @click="trigger('install')">{{ t('admin.system.discordBot.operations.install') }}</button>
      <template v-else>
        <button class="form-button primary-action" type="button" :disabled="loading || inProgress || !bot.request_available" @click="trigger('update')">{{ t('admin.system.discordBot.operations.update') }}</button>
        <button class="form-button secondary-action" type="button" :disabled="loading || inProgress || !bot.request_available" @click="trigger('restart')">{{ t('admin.system.discordBot.operations.restart') }}</button>
        <button v-if="bot.service_state !== 'active'" class="form-button secondary-action" type="button" :disabled="loading || inProgress || !bot.request_available || !config.ready" @click="trigger('start')">{{ t('admin.system.discordBot.operations.start') }}</button>
        <button v-else class="form-button danger-action" type="button" :disabled="loading || inProgress || !bot.request_available" @click="trigger('stop')">{{ t('admin.system.discordBot.operations.stop') }}</button>
      </template>
    </div>

    <form v-if="bot.installed" class="discord-bot-configuration-surface" @submit.prevent="saveConfiguration">
      <div class="staff-log-surface-head">
        <div>
          <span class="command-deck-eyebrow">{{ t('admin.system.discordBot.configuration.eyebrow') }}</span>
          <h3>{{ t('admin.system.discordBot.configuration.title') }}</h3>
          <p>{{ t('admin.system.discordBot.configuration.subtitle') }}</p>
        </div>
        <span class="summary-pill" :class="{ 'is-ready': config.valid }">{{ config.valid ? t('admin.system.discordBot.configuration.valid') : t('admin.system.discordBot.configuration.notValidated') }}</span>
      </div>

      <div class="discord-bot-secret-status-grid">
        <article><span>{{ t('admin.system.discordBot.configuration.discordToken') }}</span><strong>{{ config.discord_token_configured ? t('admin.system.discordBot.configuration.saved') : t('admin.system.discordBot.configuration.missing') }}</strong></article>
        <article><span>{{ t('admin.system.discordBot.configuration.webhookSecret') }}</span><strong>{{ config.webhook_secret_configured ? t('admin.system.discordBot.configuration.saved') : t('admin.system.discordBot.configuration.missing') }}</strong></article>
        <article><span>{{ t('admin.system.discordBot.configuration.managementToken') }}</span><strong>{{ config.management_token_configured ? t('admin.system.discordBot.configuration.generated') : t('admin.system.discordBot.configuration.pending') }}</strong></article>
      </div>

      <div class="section-fields two-fields discord-bot-config-grid">
        <label class="input-panel embedded-field">
          <span>{{ t('admin.system.discordBot.configuration.discordToken') }}</span>
          <input v-model="configurationForm.discord_bot_token" type="password" autocomplete="new-password" :placeholder="config.discord_token_configured ? t('admin.system.discordBot.configuration.keepSecret') : t('admin.system.discordBot.configuration.requiredSecret')" />
          <small>{{ t('admin.system.discordBot.configuration.discordTokenHint') }}</small>
        </label>
        <label class="input-panel embedded-field">
          <span>{{ t('admin.system.discordBot.configuration.webhookSecret') }}</span>
          <input v-model="configurationForm.webhook_secret" type="password" autocomplete="new-password" :placeholder="config.webhook_secret_configured ? t('admin.system.discordBot.configuration.keepSecret') : t('admin.system.discordBot.configuration.requiredSecret')" />
          <small>{{ t('admin.system.discordBot.configuration.webhookSecretHint') }}</small>
        </label>
        <label class="input-panel embedded-field discord-bot-wide-field">
          <span>{{ t('admin.system.discordBot.configuration.websiteUrl') }}</span>
          <input v-model="configurationForm.website_base_url" type="url" required />
          <small>{{ t('admin.system.discordBot.configuration.endpointPreview') }}: <code>{{ webhookEndpoint }}</code></small>
        </label>
      </div>

      <div class="discord-bot-channel-grid">
        <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.channels.events') }}</span><input v-model="configurationForm.events_channel_id" inputmode="numeric" required pattern="[0-9]{15,22}" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.channels.guides') }}</span><input v-model="configurationForm.guides_channel_id" inputmode="numeric" required pattern="[0-9]{15,22}" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.channels.builds') }}</span><input v-model="configurationForm.builds_channel_id" inputmode="numeric" required pattern="[0-9]{15,22}" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.channels.forum') }}</span><input v-model="configurationForm.forum_channel_id" inputmode="numeric" required pattern="[0-9]{15,22}" /></label>
        <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.channels.default') }}</span><input v-model="configurationForm.default_channel_id" inputmode="numeric" required pattern="[0-9]{15,22}" /></label>
      </div>

      <details class="discord-bot-advanced-config">
        <summary>{{ t('admin.system.discordBot.configuration.advanced') }}</summary>
        <div class="section-fields three-columns">
          <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.timestampTolerance') }}</span><input v-model.number="configurationForm.timestamp_tolerance_seconds" type="number" min="30" max="3600" /></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.timeout') }}</span><input v-model.number="configurationForm.request_timeout_seconds" type="number" min="1" max="120" step="0.5" /></label>
          <label class="input-panel embedded-field"><span>{{ t('admin.system.discordBot.configuration.attempts') }}</span><input v-model.number="configurationForm.max_attempts" type="number" min="1" max="8" /></label>
        </div>
      </details>

      <div class="discord-bot-toggle-grid">
        <label class="toggle-card"><span><strong>{{ t('admin.system.discordBot.configuration.suppressNotifications') }}</strong><small>{{ t('admin.system.discordBot.configuration.suppressNotificationsHint') }}</small></span><input v-model="configurationForm.suppress_notifications" type="checkbox" /></label>
        <label class="toggle-card"><span><strong>{{ t('admin.system.discordBot.configuration.restartAfterSave') }}</strong><small>{{ t('admin.system.discordBot.configuration.restartAfterSaveHint') }}</small></span><input v-model="configurationForm.restart_after_save" type="checkbox" /></label>
      </div>

      <div class="discord-bot-config-actions">
        <p class="muted">{{ t('admin.system.discordBot.configuration.secretNotice') }}</p>
        <button class="form-button primary-action" type="submit" :disabled="!canSaveConfiguration">{{ configurationSaving ? t('admin.system.discordBot.configuration.saving') : t('admin.system.discordBot.configuration.save') }}</button>
      </div>
    </form>

    <p v-if="success" class="success-text table-state">{{ success }}</p>
    <p v-if="error" class="error-text table-state">{{ error }}</p>

    <details class="discord-bot-log" :open="bot.state === 'failed'">
      <summary>{{ t('admin.system.discordBot.logTitle') }}</summary>
      <pre v-if="bot.log_tail?.length">{{ bot.log_tail.join('\n') }}</pre>
      <p v-else class="muted">{{ t('admin.system.discordBot.logEmpty') }}</p>
    </details>
  </section>
</template>
