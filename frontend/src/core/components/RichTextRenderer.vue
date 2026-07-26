<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { absoluteFileUrl, fileKind, formatFileSize, isEmbeddableFile } from '@/modules/files/api/files'
import { renderMarkdown } from '@/shared/content/markdown'
import { parseRichTextEmbeds } from '@/shared/content/richTextEmbeds'

const props = defineProps({
  body: {
    type: String,
    default: '',
  },
  attachments: {
    type: Array,
    default: () => [],
  },
  builds: {
    type: Array,
    default: () => [],
  },
  headingIdPrefix: {
    type: String,
    default: '',
  },
})

const { optionLabel, t } = useLocale()
const parts = computed(() => {
  let headingIndex = 0
  return parseRichTextEmbeds(props.body).map((part) => {
    if (part.type !== 'text') return part
    const html = renderMarkdown(part.text, {
      headingIdPrefix: props.headingIdPrefix,
      headingStartIndex: headingIndex,
    })
    headingIndex += String(part.text || '').split(/\r?\n/)
      .filter((line) => /^\s*#{1,6}\s+\S/.test(line)).length
    return { ...part, html }
  })
})
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
const buildMap = computed(() => {
  const map = new Map()
  for (const build of props.builds || []) {
    map.set(Number(build.id), build)
  }
  return map
})

function fileFor(part) {
  return fileMap.value.get(Number(part.fileId))
}

function buildFor(part) {
  return buildMap.value.get(Number(part.buildId))
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

function buildTypeLabel(value) {
  return t(`builds.types.${value || 'balanced'}`)
}

function crewTotal(build) {
  return build?.ship_stats?.crew_total || 0
}

function upgradeSummary(build) {
  const stats = build?.ship_stats || {}
  return t('builds.list.upgradeSummary', { used: stats.upgrade_slots_used || 0, max: stats.upgrade_slots_available || 0 })
}

function primaryWeapons(build) {
  const slots = [
    ...(build?.port_weapon_slots || []),
    ...(build?.starboard_weapon_slots || []),
    ...(build?.front_weapon_slots || []),
    ...(build?.rear_weapon_slots || []),
  ]
  return slots.slice(0, 3).map((slot) => `${optionLabel(slot.item)} ×${slot.quantity || 1}`).join(' · ') || '—'
}
</script>

<template>
  <div class="rich-text-content">
    <template v-for="(part, index) in parts" :key="`${part.type}-${index}-${part.fileId || part.buildId || index}`">
      <div v-if="part.type === 'text'" class="rich-text-copy markdown-content" v-html="part.html"></div>

      <figure
        v-else-if="part.type === 'fileEmbed' && fileFor(part)"
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

      <RouterLink
        v-else-if="part.type === 'buildEmbed' && buildFor(part)"
        class="inline-build-embed"
        :class="`inline-build-embed--${part.layout}`"
        :to="`/builds/${buildFor(part).id}`"
      >
        <span class="inline-build-eyebrow">{{ t('buildEmbeds.inlineEyebrow') }}</span>
        <span class="inline-build-title">{{ buildFor(part).build_name }}</span>
        <span class="inline-build-meta">
          {{ buildFor(part).ship.name }} · {{ t('common.rate') }} {{ buildFor(part).ship.rate }} · {{ buildTypeLabel(buildFor(part).build_type) }}
        </span>
        <span v-if="part.layout !== 'compact'" class="inline-build-stats">
          <span>{{ t('builds.list.crew', { current: crewTotal(buildFor(part)), max: buildFor(part).ship_stats?.crew_capacity || buildFor(part).ship.crew_capacity }) }}</span>
          <span>{{ upgradeSummary(buildFor(part)) }}</span>
          <span>{{ primaryWeapons(buildFor(part)) }}</span>
        </span>
        <span class="inline-build-open">{{ t('buildEmbeds.openBuild') }} →</span>
      </RouterLink>

      <span v-else-if="part.type === 'fileEmbed'" class="inline-attachment-missing">
        {{ t('files.inlineMissing', { id: part.fileId }) }}
      </span>
      <span v-else-if="part.type === 'buildEmbed'" class="inline-attachment-missing">
        {{ t('buildEmbeds.inlineMissing', { id: part.buildId }) }}
      </span>
    </template>
  </div>
</template>
