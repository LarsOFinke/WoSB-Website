<script setup>
import { reactive } from 'vue'

import { useLocale } from '@/locales'
import { fileKind, formatFileSize } from '@/modules/files/api/files'
import { embedSizes } from '@/shared/content/richTextEmbeds'

const props = defineProps({
  attachments: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['insert', 'remove'])
const { t } = useLocale()
const scaleById = reactive({})

function currentScale(fileId) {
  return scaleById[fileId] || 'large'
}

function setScale(fileId, value) {
  scaleById[fileId] = value
}

function insert(file) {
  emit('insert', { file, size: currentScale(file.id) })
}
</script>

<template>
  <div v-if="attachments.length" class="attachment-insert-panel" :aria-label="t('files.inlineTools')">
    <div class="attachment-insert-heading">
      <strong>{{ t('files.inlineTools') }}</strong>
      <span>{{ t('files.inlineToolsHint') }}</span>
    </div>

    <article v-for="file in attachments" :key="file.id" class="attachment-insert-row">
      <div class="attachment-insert-meta">
        <strong>{{ file.original_name }}</strong>
        <span>{{ t(`files.kind.${fileKind(file)}`) }}<template v-if="formatFileSize(file.size_bytes)"> · {{ formatFileSize(file.size_bytes) }}</template></span>
      </div>

      <label class="select-shell compact-select-shell attachment-scale-select">
        <select :value="currentScale(file.id)" @change="setScale(file.id, $event.target.value)">
          <option v-for="size in embedSizes" :key="size" :value="size">{{ t(`files.embedSizes.${size}`) }}</option>
        </select>
      </label>

      <div class="attachment-insert-actions">
        <button class="small-action" type="button" @click="insert(file)">{{ t('files.insertInline') }}</button>
        <button class="chip-remove" type="button" @click="emit('remove', file.id)">× {{ t('files.removeAttachment') }}</button>
      </div>
    </article>
  </div>
</template>
