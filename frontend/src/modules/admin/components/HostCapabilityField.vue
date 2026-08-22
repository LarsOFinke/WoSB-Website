<script setup>
import { useLocale } from '@/locales'

const model = defineModel({ type: String, default: '' })
const props = defineProps({
  operation: { type: String, default: '' },
})
const { t } = useLocale()
</script>

<template>
  <label class="form-field">
    <span>{{ t('admin.backups.restore.approvalToken') }}</span>
    <input v-model.trim="model" type="password" autocomplete="off" :placeholder="t('admin.backups.restore.approvalPlaceholder')">
    <small v-if="props.operation">
      <strong>{{ t('admin.backups.restore.commandTarget') }}</strong>
      <code>sudo /srv/rbf/current/infrastructure/scripts/services/arm-host-operation.sh {{ props.operation }}</code>
    </small>
  </label>
</template>
