<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { resourceComponent, resourceTarget } from '@/modules/onboarding/domain/newcomerGuideDraft'

defineProps({ folder: { type: Object, default: null } })
const { t } = useLocale()
</script>

<template>
  <section v-if="folder" class="wire-section newcomer-folder-content" aria-live="polite">
    <div class="workspace-section-heading">
      <div>
        <p class="eyebrow">{{ folder.block_type === 'text' ? t('newcomerGuide.textSection') : t('newcomerGuide.resourceSection') }}</p>
        <h2>{{ folder.title }}</h2>
      </div>
    </div>
    <RichTextRenderer v-if="folder.body" :body="folder.body" />
    <div v-if="folder.block_type === 'resources'" class="newcomer-resource-grid">
      <component
        :is="resourceComponent(resource)"
        v-for="resource in folder.resources"
        :key="resource.id"
        v-bind="resourceTarget(resource)"
        class="newcomer-resource-card"
        :class="{ 'is-unavailable': !resource.available }"
      >
        <span class="fleet-module-icon"><AppIcon :name="resource.resource_type === 'build' ? 'builds' : resource.resource_type === 'guide' ? 'guides' : 'arrow-right'" :size="20" /></span>
        <strong>{{ resource.label }}</strong>
        <small v-if="resource.description">{{ resource.description }}</small>
        <span class="newcomer-resource-open">{{ resource.available ? t('newcomerGuide.open') : t('newcomerGuide.unavailable') }} →</span>
      </component>
    </div>
  </section>
</template>
