<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { resourceComponent, resourceTarget } from '@/modules/onboarding/domain/newcomerGuideDraft'
import { resourceIcon } from '@/modules/onboarding/domain/newcomerGuidePresentation.js'

defineProps({
  folder: { type: Object, default: null },
  showResources: { type: Boolean, default: true },
})
const { t } = useLocale()
</script>

<template>
  <section v-if="folder" class="wire-section newcomer-folder-content" aria-live="polite">
    <div class="workspace-section-heading newcomer-folder-content__heading">
      <div>
        <p class="eyebrow">{{ folder.block_type === 'text' ? t('newcomerGuide.textSection') : t('newcomerGuide.resourceSection') }}</p>
        <h2>{{ folder.title }}</h2>
      </div>
      <span class="newcomer-folder-content__icon"><AppIcon name="folder" :size="25" /></span>
    </div>
    <div v-if="folder.body" class="newcomer-topic-briefing">
      <RichTextRenderer :body="folder.body" />
    </div>
    <section v-if="showResources && folder.block_type === 'resources'" class="newcomer-topic-resources" aria-labelledby="newcomer-topic-resources-title">
      <header>
        <div>
          <p class="eyebrow">{{ t('newcomerGuide.explorer.resources') }}</p>
          <h3 id="newcomer-topic-resources-title">{{ t('newcomerGuide.explorer.resourcesHeading') }}</h3>
          <p>{{ t('newcomerGuide.explorer.resourcesHint') }}</p>
        </div>
        <span class="summary-pill">{{ t('newcomerGuide.explorer.resourceCount', { count: folder.resources.length }) }}</span>
      </header>
      <div class="newcomer-resource-list">
      <component
        :is="resourceComponent(resource)"
        v-for="resource in folder.resources"
        :key="resource.id"
        v-bind="resourceTarget(resource)"
        class="newcomer-resource-row"
        :class="{ 'is-unavailable': !resource.available }"
      >
        <span class="newcomer-resource-row__icon"><AppIcon :name="resourceIcon(resource)" :size="20" /></span>
        <span class="newcomer-resource-row__copy">
          <strong>{{ resource.label }}</strong>
          <small>{{ resource.description || t('newcomerGuide.explorer.noResourceDescription') }}</small>
        </span>
        <span class="type-pill">{{ t(`newcomerGuide.editor.types.${resource.resource_type}`) }}</span>
        <span class="newcomer-resource-row__status">{{ resource.available ? t('newcomerGuide.explorer.available') : t('newcomerGuide.unavailable') }}</span>
        <AppIcon name="chevron-right" :size="18" />
      </component>
      <p v-if="!folder.resources.length" class="muted newcomer-resource-empty">{{ t('newcomerGuide.explorer.noResources') }}</p>
      </div>
    </section>
  </section>
</template>
