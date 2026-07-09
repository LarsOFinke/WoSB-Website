<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { absoluteFileUrl, fileKind, formatFileSize, isEmbeddableFile } from '@/services/files'
import { parseRichTextEmbeds } from '@/services/richTextEmbeds'

const props = defineProps({
  body: {
    type: String,
    default: '',
  },
  attachments: {
    type: Array,
    default: () => [],
  },
})

const { t } = useLocale()
const parts = computed(() => parseRichTextEmbeds(props.body))
const fileMap = computed(() => {
  const map = new Map()
  for (const file of props.attachments || []) {
    map.set(Number(file.id), {
      ...file,
      embedUrl: absoluteFileUrl(file.public_url),
      kind: fileKind(file),
      sizeLabel: formatFileSize(file.size_bytes),
      canEmbed: isEmbeddableFile(file),
    })
  }
  return map
})

function fileFor(part) {
  return fileMap.value.get(Number(part.fileId))
}

function isImage(file) {
  return file?.kind === 'image'
}

function isVideo(file) {
  return file?.kind === 'video'
}

function isDocument(file) {
  return file?.kind === 'pdf' || file?.kind === 'text'
}
</script>

<template>
  <div class="rich-text-content">
    <template v-for="(part, index) in parts" :key="`${part.type}-${index}-${part.fileId || index}`">
      <span v-if="part.type === 'text'" class="rich-text-copy preserve-lines">{{ part.text }}</span>

      <figure
        v-else-if="fileFor(part)"
        class="inline-attachment-embed"
        :class="[`inline-attachment-embed--${part.size}`, `inline-attachment-embed--${fileFor(part).kind}`]"
      >
        <a class="inline-attachment-title" :href="fileFor(part).embedUrl" target="_blank" rel="noopener">
          <span>{{ fileFor(part).original_name }}</span>
          <small>{{ t(`files.kind.${fileFor(part).kind}`) }}<template v-if="fileFor(part).sizeLabel"> · {{ fileFor(part).sizeLabel }}</template></small>
        </a>

        <img v-if="isImage(fileFor(part))" :src="fileFor(part).embedUrl" :alt="fileFor(part).original_name" loading="lazy" />
        <video v-else-if="isVideo(fileFor(part))" :src="fileFor(part).embedUrl" controls preload="metadata" />
        <iframe
          v-else-if="isDocument(fileFor(part))"
          class="inline-attachment-document-frame"
          :src="fileFor(part).embedUrl"
          :title="fileFor(part).original_name"
          loading="lazy"
        ></iframe>
        <a v-else class="attachment-file-link" :href="fileFor(part).embedUrl" target="_blank" rel="noopener">
          {{ t('files.openAttachment') }}
        </a>
      </figure>

      <span v-else class="inline-attachment-missing">
        {{ t('files.inlineMissing', { id: part.fileId }) }}
      </span>
    </template>
  </div>
</template>
