<script setup>
import { ref } from 'vue'

import { useLocale } from '@/locales'
import { uploadFile } from '@/services/files'

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

async function handleFiles(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const file of files) {
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
        accept="image/jpeg,image/png,image/gif,image/webp,image/svg+xml,video/mp4,video/webm,video/quicktime,application/pdf,text/plain"
        :disabled="uploading"
        @change="handleFiles"
      />
    </label>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>
