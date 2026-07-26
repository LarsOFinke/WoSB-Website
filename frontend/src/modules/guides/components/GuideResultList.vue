<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import { formatGuideDate } from '@/modules/guides/domain/guidePresentation'

defineProps({
  guides: { type: Array, required: true },
})

const { t } = useLocale()

function categoryLabel(value) {
  return t(`guides.categories.${value || 'general'}`)
}
</script>

<template>
  <div class="guide-result-list">
    <div class="guide-result-columns" aria-hidden="true">
      <span>{{ t('common.guides') }}</span>
      <span>{{ t('guides.print.author') }}</span>
      <span>{{ t('guides.print.updated') }}</span>
      <span>{{ t('files.attachments') }}</span>
    </div>

    <RouterLink
      v-for="guide in guides"
      :key="guide.id"
      class="guide-result-row"
      :to="`/guides/${guide.id}`"
    >
      <span class="guide-result-mark"><AppIcon name="guides" :size="20" /></span>
      <span class="guide-result-copy">
        <strong>{{ guide.title }}</strong>
        <small>{{ categoryLabel(guide.category) }}</small>
        <span>{{ guide.summary || t('guides.list.noSummary') }}</span>
      </span>
      <span class="guide-result-author">{{ guide.owner.display_name }}</span>
      <time class="guide-result-date" :datetime="guide.updated_at || guide.created_at">
        {{ formatGuideDate(guide.updated_at || guide.created_at) }}
      </time>
      <span class="guide-result-resources">
        <span v-if="guide.attachment_count">{{ t('guides.list.attachments', { count: guide.attachment_count }) }}</span>
        <span v-if="guide.build_reference_count">{{ t('buildEmbeds.referenceCount', { count: guide.build_reference_count }) }}</span>
        <span v-if="!guide.attachment_count && !guide.build_reference_count">—</span>
      </span>
      <AppIcon class="guide-result-arrow" name="chevron-right" :size="18" />
    </RouterLink>
  </div>
</template>
