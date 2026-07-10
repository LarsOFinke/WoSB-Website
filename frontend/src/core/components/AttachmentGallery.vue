<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { absoluteFileUrl, fileKind, formatFileSize, isEmbeddableFile } from '@/modules/files/api/files'

const props = defineProps({
  attachments: {
    type: Array,
    default: () => [],
  },
})

const { t } = useLocale()
const visibleAttachments = computed(() =>
  (props.attachments || []).map((file) => ({
    ...file,
    embedUrl: absoluteFileUrl(file.public_url),
    kind: fileKind(file),
    sizeLabel: formatFileSize(file.size_bytes),
    canEmbed: isEmbeddableFile(file),
  })),
)

function isImage(file) {
  return file.kind === 'image'
}

function isVideo(file) {
  return file.kind === 'video'
}

function isDocument(file) {
  return file.kind === 'pdf' || file.kind === 'text'
}
</script>

<template>
  <div v-if="visibleAttachments.length" class="attachment-gallery" :aria-label="t('files.attachments')">
    <article
      v-for="file in visibleAttachments"
      :key="file.id"
      class="attachment-card"
      :class="[`attachment-card--${file.kind}`, { 'attachment-card--embedded': file.canEmbed }]"
    >
      <a class="attachment-card-title" :href="file.embedUrl" target="_blank" rel="noopener">
        <span>{{ file.original_name }}</span>
        <small>{{ t(`files.kind.${file.kind}`) }}<template v-if="file.sizeLabel"> · {{ file.sizeLabel }}</template></small>
      </a>

      <img v-if="isImage(file)" :src="file.embedUrl" :alt="file.original_name" loading="lazy" />
      <video v-else-if="isVideo(file)" :src="file.embedUrl" controls preload="metadata" />
      <iframe
        v-else-if="isDocument(file)"
        class="attachment-document-frame"
        :src="file.embedUrl"
        :title="file.original_name"
        loading="lazy"
      ></iframe>
      <a v-else class="attachment-file-link" :href="file.embedUrl" target="_blank" rel="noopener">
        {{ t('files.openAttachment') }}
      </a>
    </article>
  </div>
</template>
