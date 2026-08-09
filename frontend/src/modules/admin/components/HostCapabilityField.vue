<script setup>
import { useLocale } from '@/locales'

const model = defineModel({ type: String, default: '' })
const { t } = useLocale()
</script>

<template>
  <label class="form-field">
    <span>{{ t('admin.backups.restore.approvalToken') }}</span>
    <input v-model.trim="model" type="password" autocomplete="off" :placeholder="t('admin.backups.restore.approvalPlaceholder')">
  </label>
</template>
