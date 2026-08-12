<script setup>
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import { useLocale } from '@/locales'

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
  <section v-if="folder" class="wire-section newcomer-folder-editor" aria-live="polite">
    <div class="workspace-section-heading compact-heading">
      <div>
        <p class="eyebrow">{{ t('newcomerGuide.editor.selectedFolder', { index: folderIndex + 1 }) }}</p>
        <h2>{{ folder.title || t('newcomerGuide.editor.untitled') }}</h2>
        <p class="section-helper-text">{{ t('newcomerGuide.editor.orderHint') }}</p>
      </div>
    </div>

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
      <MarkdownEditor v-model="folder.body" :rows="7" :maxlength="20000" :required="folder.block_type === 'text'" />
    </div>

    <div v-if="folder.block_type === 'resources'" class="newcomer-resource-editor-list">
      <div class="newcomer-resource-list-heading">
        <div>
          <h3>{{ t('newcomerGuide.editor.folderResources') }}</h3>
          <p class="section-helper-text">{{ t('newcomerGuide.editor.resourceOrderHint') }}</p>
        </div>
        <button class="form-button secondary-action" type="button" @click="$emit('add-resource', folder)">{{ t('newcomerGuide.editor.addResource') }}</button>
      </div>
      <p v-if="resourceOptionsLoading" class="muted section-helper-text">{{ t('newcomerGuide.editor.loadingResources') }}</p>
      <p v-else-if="resourceOptionsError" class="error-text section-helper-text">{{ resourceOptionsError }}</p>
      <article v-for="(resource, resourceIndex) in folder.resources" :key="`resource-${resourceIndex}`" class="newcomer-resource-editor-row">
        <div class="newcomer-resource-editor-head">
          <strong>{{ t('newcomerGuide.editor.resource', { index: resourceIndex + 1 }) }}</strong>
          <div class="compact-actions">
            <button type="button" :disabled="resourceIndex === 0" :aria-label="t('newcomerGuide.editor.moveUp')" @click="$emit('move-resource', folder, resourceIndex, -1)">↑</button>
            <button type="button" :disabled="resourceIndex === folder.resources.length - 1" :aria-label="t('newcomerGuide.editor.moveDown')" @click="$emit('move-resource', folder, resourceIndex, 1)">↓</button>
            <button type="button" @click="$emit('remove-resource', folder, resourceIndex)">{{ t('common.remove') }}</button>
          </div>
        </div>
        <div class="directory-form-grid">
          <label class="input-panel embedded-field">
            <span>{{ t('common.type') }}</span>
            <select v-model="resource.resource_type" @change="$emit('resource-type-change', resource)">
              <option v-for="entry in resourceTypeOptions" :key="entry.value" :value="entry.value">{{ entry.label }}</option>
            </select>
          </label>
          <label v-if="resource.resource_type === 'guide'" class="input-panel embedded-field">
            <span>{{ t('common.guides') }}</span>
            <select v-model="resource.resource_id" required :disabled="resourceOptionsLoading">
              <option :value="null">{{ guides.length ? t('common.empty') : t('newcomerGuide.editor.noGuides') }}</option>
              <option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option>
            </select>
          </label>
          <label v-else-if="resource.resource_type === 'build'" class="input-panel embedded-field">
            <span>{{ t('common.builds') }}</span>
            <select v-model="resource.resource_id" required :disabled="resourceOptionsLoading">
              <option :value="null">{{ builds.length ? t('common.empty') : t('newcomerGuide.editor.noBuilds') }}</option>
              <option v-for="build in builds" :key="build.id" :value="build.id">{{ build.build_name }}</option>
            </select>
          </label>
          <label v-else class="input-panel embedded-field">
            <span>{{ t('newcomerGuide.editor.url') }}</span>
            <input v-model="resource.url" maxlength="500" required :placeholder="resource.resource_type === 'internal' ? '/guides' : 'https://…'" />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('newcomerGuide.editor.customLabel') }}</span>
            <input v-model="resource.label" maxlength="180" :placeholder="t('newcomerGuide.editor.customLabelHint')" />
          </label>
        </div>
        <label class="input-panel embedded-field">
          <span>{{ t('common.description') }}</span>
          <textarea v-model="resource.description" rows="2" maxlength="500" />
        </label>
      </article>
      <p v-if="!folder.resources.length" class="muted newcomer-resource-empty">{{ t('newcomerGuide.editor.emptyResources') }}</p>
    </div>
  </section>
  <section v-else class="wire-section newcomer-folder-editor newcomer-folder-editor--empty">
    <span class="fleet-module-icon" aria-hidden="true">+</span>
    <h2>{{ t('newcomerGuide.editor.noFolderTitle') }}</h2>
    <p class="muted">{{ t('newcomerGuide.editor.noFolderText') }}</p>
  </section>
</template>
