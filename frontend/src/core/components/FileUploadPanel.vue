<script setup>
import { computed, ref } from 'vue'

import { useLocale } from '@/locales'
import { ACCEPT_ATTRIBUTE, formatFileSize, maxBytesForFile, uploadFile, validateFileForUpload } from '@/modules/files/api/files'

const props = defineProps({
  usageContext: {
    type: String,
    default: 'general',
  },
  acceptedTypes: {
    type: Array,
    default: null,
  },
  multiple: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['uploaded'])
const { t } = useLocale()
const uploading = ref(false)
const error = ref('')
const acceptAttribute = computed(() => (props.acceptedTypes?.length ? props.acceptedTypes.join(',') : ACCEPT_ATTRIBUTE))

function validationMessage(file, result) {
  if (result.reason === 'name') return t('files.validation.unsafeName', { name: file.name })
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
      const validation = props.acceptedTypes?.length && !props.acceptedTypes.includes(String(file.type || '').toLowerCase())
        ? { valid: false, reason: 'type' }
        : validateFileForUpload(file)
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
        :multiple="multiple"
        :accept="acceptAttribute"
        :disabled="uploading"
        @change="handleFiles"
      />
    </label>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>
