<script setup>
import { ref } from 'vue'

import { useLocale } from '@/locales'
import { ACCEPT_ATTRIBUTE, formatFileSize, maxBytesForFile, uploadFile, validateFileForUpload } from '@/services/files'

const props = defineProps({
  usageContext: {
    type: String,
    default: 'general',
  },
})

const emit = defineEmits(['uploaded'])
const { t } = useLocale()
const uploading = ref(false)
const error = ref('')

function validationMessage(file, result) {
  if (result.reason === 'type') return t('files.validation.unsupportedType', { name: file.name })
  if (result.reason === 'empty') return t('files.validation.empty', { name: file.name })
  if (result.reason === 'size') return t('files.validation.tooLarge', { name: file.name, limit: formatFileSize(maxBytesForFile(file)) })
  return t('files.uploadError')
}

async function handleFiles(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const file of files) {
      const validation = validateFileForUpload(file)
      if (!validation.valid) {
        error.value = validationMessage(file, validation)
        continue
      }
      const uploaded = await uploadFile(file, props.usageContext)
      emit('uploaded', uploaded)
    }
  } catch (err) {
    error.value = err.message || t('files.uploadError')
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}
</script>

<template>
  <div class="file-upload-panel">
    <label class="file-drop-box">
      <span>{{ uploading ? t('files.uploading') : t('files.upload') }}</span>
      <small>{{ t('files.allowed') }}</small>
      <input
        type="file"
        multiple
        :accept="ACCEPT_ATTRIBUTE"
        :disabled="uploading"
        @change="handleFiles"
      />
    </label>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>
