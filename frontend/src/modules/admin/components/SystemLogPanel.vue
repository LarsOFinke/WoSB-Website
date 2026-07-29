<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import SecurityLogDashboard from '@/modules/admin/components/SecurityLogDashboard.vue'

const props = defineProps({
  workspace: { type: Object, required: true },
})

const emit = defineEmits(['block-ip'])
const { t } = useLocale()

function model(key) {
  return computed({
    get: () => props.workspace[key].value,
    set: (value) => { props.workspace[key].value = value },
  })
}

const logIp = model('logIp')
const logThreat = model('logThreat')
const logFromDate = model('logFromDate')
const logToDate = model('logToDate')
</script>

<template>
  <section class="system-log-panel security-candidate-panel">
    <div class="admin-panel-heading system-log-heading">
      <div>
        <h2>{{ t('admin.logs.title') }}</h2>
        <p>{{ t('admin.logs.subtitle') }}</p>
      </div>
      <span class="summary-pill">{{ workspace.logsCountLabel.value }}</span>
    </div>

    <aside class="security-privacy-notice" role="note">
      <strong>{{ t('admin.logs.privacyTitle') }}</strong>
      <p>{{ t('admin.logs.privacyText') }}</p>
    </aside>

    <SecurityLogDashboard
      v-model:from-date="logFromDate"
      v-model:to-date="logToDate"
      v-model:threat-level="logThreat"
      v-model:selected-ip="logIp"
      :can-block="true"
      @dashboard-update="workspace.applyDashboardSummary"
      @block-ip="emit('block-ip', $event)"
    />
  </section>
</template>
