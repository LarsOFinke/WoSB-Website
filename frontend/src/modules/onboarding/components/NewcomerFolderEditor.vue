<script setup>
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import { useLocale } from '@/locales'
import NewcomerResourceEditor from '@/modules/onboarding/components/NewcomerResourceEditor.vue'

defineProps({
  folder: { type: Object, default: null },
  folderIndex: { type: Number, default: 0 },
  guides: { type: Array, default: () => [] },
  builds: { type: Array, default: () => [] },
  resourceTypeOptions: { type: Array, default: () => [] },
  resourceOptionsLoading: { type: Boolean, default: false },
  resourceOptionsError: { type: String, default: '' },
})

defineEmits(['add-resource', 'remove-resource', 'move-resource', 'resource-type-change'])
const { t } = useLocale()
</script>

<template>
  <section v-if="folder" class="newcomer-folder-editor" aria-live="polite">
    <header class="newcomer-folder-editor-heading">
      <div>
        <p class="eyebrow">{{ t('newcomerGuide.editor.selectedFolder', { index: folderIndex + 1 }) }}</p>
        <h2>{{ folder.title || t('newcomerGuide.editor.untitled') }}</h2>
        <p class="section-helper-text">{{ t('newcomerGuide.editor.orderHint') }}</p>
      </div>
      <span class="summary-pill">{{ t(folder.block_type === 'text' ? 'newcomerGuide.editor.textBlock' : 'newcomerGuide.editor.resourceBlock') }}</span>
    </header>

    <section class="newcomer-section-fields">
      <div class="directory-form-grid newcomer-block-fields">
        <label class="input-panel embedded-field">
          <span>{{ t('common.title') }}</span>
          <input v-model="folder.title" maxlength="180" required />
        </label>
        <label class="input-panel embedded-field">
          <span>{{ t('newcomerGuide.editor.blockType') }}</span>
          <select v-model="folder.block_type">
            <option value="text">{{ t('newcomerGuide.editor.textBlock') }}</option>
            <option value="resources">{{ t('newcomerGuide.editor.resourceBlock') }}</option>
          </select>
        </label>
      </div>

      <div class="newcomer-markdown-field">
        <span class="field-label">{{ folder.block_type === 'text' ? t('newcomerGuide.editor.text') : t('newcomerGuide.editor.optionalIntro') }}</span>
        <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
        <MarkdownEditor v-model="folder.body" :rows="9" :maxlength="20000" :required="folder.block_type === 'text'" />
      </div>
    </section>

    <section v-if="folder.block_type === 'resources'" class="newcomer-resource-editor-list">
      <header class="newcomer-resource-list-heading">
        <div>
          <h3>{{ t('newcomerGuide.editor.folderResources') }}</h3>
          <p class="section-helper-text">{{ t('newcomerGuide.editor.resourceOrderHint') }}</p>
        </div>
        <button class="form-button secondary-action" type="button" @click="$emit('add-resource', folder)">+ {{ t('newcomerGuide.editor.addResource') }}</button>
      </header>
      <p v-if="resourceOptionsLoading" class="muted section-helper-text">{{ t('newcomerGuide.editor.loadingResources') }}</p>
      <p v-else-if="resourceOptionsError" class="error-text section-helper-text">{{ resourceOptionsError }}</p>
      <NewcomerResourceEditor
        v-for="(resource, resourceIndex) in folder.resources" :key="resource._key || `resource-${resourceIndex}`"
        :resource="resource" :resource-index="resourceIndex" :resource-count="folder.resources.length"
        :guides="guides" :builds="builds" :resource-type-options="resourceTypeOptions"
        :resource-options-loading="resourceOptionsLoading"
        @remove="$emit('remove-resource', folder, $event)"
        @move="(index, delta) => $emit('move-resource', folder, index, delta)"
        @type-change="$emit('resource-type-change', $event)"
      />
      <p v-if="!folder.resources.length" class="muted newcomer-resource-empty">{{ t('newcomerGuide.editor.emptyResources') }}</p>
    </section>
  </section>

  <section v-else class="newcomer-folder-editor newcomer-folder-editor--empty">
    <span class="fleet-module-icon" aria-hidden="true">+</span>
    <h2>{{ t('newcomerGuide.editor.noFolderTitle') }}</h2>
    <p class="muted">{{ t('newcomerGuide.editor.noFolderText') }}</p>
  </section>
</template>
