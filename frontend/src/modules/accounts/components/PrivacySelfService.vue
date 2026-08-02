<script setup>
import { useLocale } from '@/locales'
import { usePrivacySelfService } from '@/modules/accounts/composables/usePrivacySelfService'

const props = defineProps({ username: { type: String, required: true } })
const { t } = useLocale()
const workspace = usePrivacySelfService({ t, username: props.username })
</script>

<template>
  <details class="profile-refresh-security privacy-self-service">
    <summary><h3>{{ t('privacy.data.title') }}</h3></summary>
    <div class="profile-refresh-password">
      <p class="muted">{{ t('privacy.data.description') }}</p>
      <button class="form-button" type="button" :disabled="workspace.busy.value === 'export'" @click="workspace.downloadExport">
        {{ t('privacy.data.export') }}
      </button>
      <form @submit.prevent="workspace.submitRequest">
        <label class="input-panel embedded-field">
          <span>{{ t('privacy.data.requestType') }}</span>
          <select v-model="workspace.form.request_type">
            <option value="correction">{{ t('privacy.data.correction') }}</option>
            <option value="deletion">{{ t('privacy.data.deletion') }}</option>
          </select>
        </label>
        <label class="input-panel embedded-field">
          <span>{{ t('privacy.data.details') }}</span>
          <textarea v-model="workspace.form.details" maxlength="4000" rows="4" required></textarea>
        </label>
        <label v-if="workspace.form.request_type === 'deletion'" class="input-panel embedded-field">
          <span>{{ t('privacy.data.confirmation', { username }) }}</span>
          <input v-model="workspace.form.confirmation" maxlength="80" required />
        </label>
        <button class="form-button" type="submit" :disabled="workspace.busy.value === 'request'">{{ t('privacy.data.submit') }}</button>
      </form>
      <p v-if="workspace.error.value" class="error-text">{{ workspace.error.value }}</p>
      <p v-if="workspace.success.value" class="success-text">{{ workspace.success.value }}</p>
      <ul v-if="workspace.requests.value.length" class="plain-list">
        <li v-for="request in workspace.requests.value" :key="request.id">
          {{ t(`privacy.data.types.${request.request_type}`) }} · {{ t(`privacy.data.status.${request.status}`) }}
        </li>
      </ul>
    </div>
  </details>
</template>
