<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { createIpBlock, getIpBlockSummary, listIpBlocks, unblockIpBlock } from '@/modules/admin/api/admin'

const props = defineProps({
  initialIp: { type: String, default: '' },
  canManage: { type: Boolean, default: false },
})

const emit = defineEmits(['consumed-initial-ip', 'changed'])
const { locale, t } = useLocale()

const rows = ref([])
const summary = ref({ total: 0, active: 0, permanent: 0, temporary: 0, expired: 0, unblocked: 0 })
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const statusFilter = ref('active')
const search = ref('')
const pendingUnblockId = ref(null)
const unblockReason = ref('')
let searchTimer = null

const form = reactive({
  ip_address: '',
  reason: '',
  notes: '',
  duration: 'permanent',
  custom_expires_at: '',
})

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function expirationForDuration() {
  if (form.duration === 'permanent') return null
  if (form.duration === 'custom') return form.custom_expires_at ? new Date(form.custom_expires_at).toISOString() : null
  const hours = Number(form.duration)
  const expires = new Date()
  expires.setHours(expires.getHours() + hours)
  return expires.toISOString()
}

function statusLabel(row) {
  if (row.is_active) return row.is_temporary ? t('admin.ipBlocks.status.temporary') : t('admin.ipBlocks.status.permanent')
  if (row.is_expired) return t('admin.ipBlocks.status.expired')
  return t('admin.ipBlocks.status.unblocked')
}

function resetForm() {
  form.ip_address = ''
  form.reason = ''
  form.notes = ''
  form.duration = 'permanent'
  form.custom_expires_at = ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [list, totals] = await Promise.all([
      listIpBlocks({ status: statusFilter.value, search: search.value, limit: 300 }),
      getIpBlockSummary(),
    ])
    rows.value = list
    summary.value = totals
  } catch (err) {
    error.value = err.message || t('admin.ipBlocks.loadError')
  } finally {
    loading.value = false
  }
}

async function submitBlock() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const expiresAt = expirationForDuration()
    if (form.duration === 'custom' && !expiresAt) {
      throw new Error(t('admin.ipBlocks.customExpiryRequired'))
    }
    await createIpBlock({
      ip_address: form.ip_address,
      reason: form.reason,
      notes: form.notes || null,
      expires_at: expiresAt,
    })
    success.value = t('admin.ipBlocks.created')
    resetForm()
    statusFilter.value = 'active'
    await load()
    emit('changed')
  } catch (err) {
    error.value = err.message || t('admin.ipBlocks.createError')
  } finally {
    saving.value = false
  }
}

function requestUnblock(id) {
  pendingUnblockId.value = id
  unblockReason.value = ''
}

function cancelUnblock() {
  pendingUnblockId.value = null
  unblockReason.value = ''
}

async function confirmUnblock(id) {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await unblockIpBlock(id, unblockReason.value)
    success.value = t('admin.ipBlocks.unblocked')
    cancelUnblock()
    await load()
    emit('changed')
  } catch (err) {
    error.value = err.message || t('admin.ipBlocks.unblockError')
  } finally {
    saving.value = false
  }
}

function useInitialIp(value) {
  if (!value) return
  form.ip_address = value
  emit('consumed-initial-ip')
  requestAnimationFrame(() => document.querySelector('#ip-block-address')?.focus())
}

watch(() => props.initialIp, useInitialIp, { immediate: true })
watch(statusFilter, load)
watch(search, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(load, 250)
})
onMounted(load)
onBeforeUnmount(() => window.clearTimeout(searchTimer))
</script>

<template>
  <section class="ip-block-management" :aria-label="t('admin.ipBlocks.title')">
    <div class="admin-panel-heading ip-block-heading">
      <div>
        <h2>{{ t('admin.ipBlocks.title') }}</h2>
        <p>{{ t('admin.ipBlocks.subtitle') }}</p>
      </div>
      <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
    </div>

    <div class="ip-block-summary-grid">
      <article><span>{{ t('admin.ipBlocks.summary.active') }}</span><strong>{{ summary.active }}</strong><small>{{ t('admin.ipBlocks.summary.activeHint') }}</small></article>
      <article><span>{{ t('admin.ipBlocks.summary.permanent') }}</span><strong>{{ summary.permanent }}</strong><small>{{ t('admin.ipBlocks.summary.permanentHint') }}</small></article>
      <article><span>{{ t('admin.ipBlocks.summary.temporary') }}</span><strong>{{ summary.temporary }}</strong><small>{{ t('admin.ipBlocks.summary.temporaryHint') }}</small></article>
      <article><span>{{ t('admin.ipBlocks.summary.history') }}</span><strong>{{ summary.expired + summary.unblocked }}</strong><small>{{ t('admin.ipBlocks.summary.historyHint') }}</small></article>
    </div>

    <div class="ip-block-workspace-grid" :class="{ 'is-read-only': !canManage }">
      <form v-if="canManage" class="ip-block-form" @submit.prevent="submitBlock">
        <div class="ip-block-section-head">
          <div><span class="command-deck-eyebrow">{{ t('admin.ipBlocks.createEyebrow') }}</span><h3>{{ t('admin.ipBlocks.createTitle') }}</h3></div>
          <span class="summary-pill">{{ t('admin.ipBlocks.exactOnly') }}</span>
        </div>
        <label class="input-panel embedded-field">
          <span>{{ t('admin.ipBlocks.ipAddress') }}</span>
          <input id="ip-block-address" v-model="form.ip_address" required maxlength="64" inputmode="decimal" autocomplete="off" :placeholder="t('admin.ipBlocks.ipPlaceholder')" />
        </label>
        <label class="input-panel embedded-field">
          <span>{{ t('admin.ipBlocks.reason') }}</span>
          <input v-model="form.reason" required minlength="3" maxlength="240" :placeholder="t('admin.ipBlocks.reasonPlaceholder')" />
        </label>
        <div class="ip-block-duration-grid">
          <label class="input-panel embedded-field select-shell">
            <span>{{ t('admin.ipBlocks.duration') }}</span>
            <select v-model="form.duration">
              <option value="permanent">{{ t('admin.ipBlocks.durations.permanent') }}</option>
              <option value="1">{{ t('admin.ipBlocks.durations.oneHour') }}</option>
              <option value="24">{{ t('admin.ipBlocks.durations.oneDay') }}</option>
              <option value="168">{{ t('admin.ipBlocks.durations.sevenDays') }}</option>
              <option value="720">{{ t('admin.ipBlocks.durations.thirtyDays') }}</option>
              <option value="custom">{{ t('admin.ipBlocks.durations.custom') }}</option>
            </select>
          </label>
          <label v-if="form.duration === 'custom'" class="input-panel embedded-field">
            <span>{{ t('admin.ipBlocks.expiresAt') }}</span>
            <input v-model="form.custom_expires_at" type="datetime-local" required />
          </label>
        </div>
        <label class="input-panel embedded-field">
          <span>{{ t('admin.ipBlocks.notes') }}</span>
          <textarea v-model="form.notes" rows="4" maxlength="2000" :placeholder="t('admin.ipBlocks.notesPlaceholder')"></textarea>
        </label>
        <p class="muted ip-block-safety-note">{{ t('admin.ipBlocks.safetyNote') }}</p>
        <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('admin.ipBlocks.saving') : t('admin.ipBlocks.blockAction') }}</button>
      </form>

      <article v-else class="ip-block-read-only-note">
        <span class="command-deck-eyebrow">{{ t('admin.ipBlocks.readOnlyEyebrow') }}</span>
        <h3>{{ t('admin.ipBlocks.readOnlyTitle') }}</h3>
        <p>{{ t('admin.ipBlocks.readOnlyHint') }}</p>
      </article>

      <section class="ip-block-list-panel">
        <div class="ip-block-section-head">
          <div><span class="command-deck-eyebrow">{{ t('admin.ipBlocks.listEyebrow') }}</span><h3>{{ t('admin.ipBlocks.listTitle') }}</h3></div>
          <span class="summary-pill">{{ rows.length }}</span>
        </div>
        <div class="staff-filter-row ip-block-filter-row">
          <label class="filter-box select-shell">
            <select v-model="statusFilter">
              <option value="active">{{ t('admin.ipBlocks.filters.active') }}</option>
              <option value="expired">{{ t('admin.ipBlocks.filters.expired') }}</option>
              <option value="unblocked">{{ t('admin.ipBlocks.filters.unblocked') }}</option>
              <option value="all">{{ t('admin.ipBlocks.filters.all') }}</option>
            </select>
          </label>
          <label class="filter-box admin-search"><input v-model="search" type="search" :placeholder="t('admin.ipBlocks.searchPlaceholder')" /></label>
        </div>

        <p v-if="error" class="error-text table-state">{{ error }}</p>
        <p v-if="success" class="success-text table-state">{{ success }}</p>
        <p v-if="loading" class="muted table-state">{{ t('admin.ipBlocks.loading') }}</p>
        <p v-else-if="rows.length === 0" class="muted table-state">{{ t('admin.ipBlocks.empty') }}</p>

        <div v-else class="ip-block-card-list">
          <article v-for="row in rows" :key="row.id" class="ip-block-card" :class="{ 'is-inactive': !row.is_active }">
            <div class="ip-block-card-main">
              <div class="ip-block-card-title">
                <strong>{{ row.ip_address }}</strong>
                <span class="ip-block-status-pill" :class="{ 'is-active': row.is_active, 'is-expired': row.is_expired }">{{ statusLabel(row) }}</span>
              </div>
              <p>{{ row.reason }}</p>
              <small>{{ t('admin.ipBlocks.createdBy', { user: row.created_by_username, date: formatDateTime(row.created_at) }) }}</small>
              <small v-if="row.expires_at">{{ t('admin.ipBlocks.expires', { date: formatDateTime(row.expires_at) }) }}</small>
              <small v-if="row.unblocked_at">{{ t('admin.ipBlocks.unblockedBy', { user: row.unblocked_by_username || '—', date: formatDateTime(row.unblocked_at) }) }}</small>
              <small v-if="row.notes" class="ip-block-notes">{{ row.notes }}</small>
            </div>
            <div class="ip-block-card-actions">
              <button v-if="canManage && row.is_active && pendingUnblockId !== row.id" class="small-action" type="button" @click="requestUnblock(row.id)">{{ t('admin.ipBlocks.unblockAction') }}</button>
              <div v-else-if="canManage && row.is_active" class="ip-unblock-confirmation">
                <input v-model="unblockReason" maxlength="240" :placeholder="t('admin.ipBlocks.unblockReasonPlaceholder')" />
                <div class="hero-actions">
                  <button class="small-action primary-action" type="button" :disabled="saving" @click="confirmUnblock(row.id)">{{ t('admin.ipBlocks.confirmUnblock') }}</button>
                  <button class="small-action" type="button" @click="cancelUnblock">{{ t('common.cancel') }}</button>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
