<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getDiscordBotStatus, requestDiscordBotOperation } from '@/modules/admin/api/admin'

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
})
const loading = ref(false)
const error = ref('')
const success = ref('')
let pollTimer = null

const inProgress = computed(() => ['queued', 'running'].includes(bot.value.state))
const stateLabel = computed(() => t(`admin.system.states.${bot.value.state || 'idle'}`))
const serviceLabel = computed(() => t(`admin.system.discordBot.serviceStates.${bot.value.service_state || 'unknown'}`))

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function schedulePoll() {
  window.clearTimeout(pollTimer)
  if (!inProgress.value) return
  pollTimer = window.setTimeout(async () => {
    await loadStatus()
    schedulePoll()
  }, 3000)
}

async function loadStatus() {
  loading.value = true
  error.value = ''
  try {
    bot.value = await getDiscordBotStatus()
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

    <div class="discord-bot-status-grid">
      <article class="home-status-card refined-status-card discord-bot-status-card">
        <span>{{ t('admin.system.discordBot.managerState') }}</span>
        <strong>{{ stateLabel }}</strong>
        <p>{{ bot.message || t('admin.system.discordBot.notConfigured') }}</p>
        <div class="discord-bot-badge-row">
          <span class="summary-pill" :class="{ 'is-ready': bot.configured }">{{ bot.configured ? t('admin.system.discordBot.configured') : t('admin.system.discordBot.configurationMissing') }}</span>
          <span class="summary-pill" :class="{ 'is-ready': bot.installed }">{{ bot.installed ? t('admin.system.discordBot.installed') : t('admin.system.discordBot.notInstalled') }}</span>
          <span class="summary-pill" :class="{ 'is-ready': bot.service_state === 'active' }">{{ serviceLabel }}</span>
        </div>
      </article>

      <article class="home-status-card refined-status-card discord-bot-detail-card">
        <span>{{ t('admin.system.discordBot.runtime') }}</span>
        <dl class="system-update-meta">
          <div><dt>{{ t('admin.system.discordBot.version') }}</dt><dd>{{ bot.version || '—' }}</dd></div>
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
        <button v-if="bot.service_state !== 'active'" class="form-button secondary-action" type="button" :disabled="loading || inProgress || !bot.request_available" @click="trigger('start')">{{ t('admin.system.discordBot.operations.start') }}</button>
        <button v-else class="form-button danger-action" type="button" :disabled="loading || inProgress || !bot.request_available" @click="trigger('stop')">{{ t('admin.system.discordBot.operations.stop') }}</button>
      </template>
    </div>

    <p v-if="success" class="success-text table-state">{{ success }}</p>
    <p v-if="error" class="error-text table-state">{{ error }}</p>

    <details class="discord-bot-log" :open="bot.state === 'failed'">
      <summary>{{ t('admin.system.discordBot.logTitle') }}</summary>
      <pre v-if="bot.log_tail?.length">{{ bot.log_tail.join('\n') }}</pre>
      <p v-else class="muted">{{ t('admin.system.discordBot.logEmpty') }}</p>
    </details>
  </section>
</template>
