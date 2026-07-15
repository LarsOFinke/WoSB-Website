<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useNewcomerGuidePage } from '@/modules/onboarding/composables/useNewcomerGuidePage.js'

const {
  t, isStaff, page, draft, guides,
  builds, loading, saving, editing, error,
  success, resourceOptionsLoading, resourceOptionsLoaded, resourceOptionsError, resourceTypeOptions,
  emptyTextBlock, emptyResourceBlock, emptyResource, toDraft, normalizePayload,
  resourceComponent, resourceTarget, loadResourceOptions, startEditing, cancelEditing,
  addBlock, removeBlock, moveBlock, addResource, addLinkedResource,
  removeResource, moveResource, onResourceTypeChange, loadPage, savePage,
} = useNewcomerGuidePage()
</script>

<template>
  <section class="newcomer-guide-page" aria-labelledby="newcomer-guide-title">
    <div class="wire-frame page-frame newcomer-guide-frame">
      <PageHeader
        :eyebrow="t('newcomerGuide.eyebrow')"
        :title="page?.title || t('newcomerGuide.title')"
        :description="page?.intro || t('newcomerGuide.subtitle')"
        title-id="newcomer-guide-title"
      >
        <template #meta>
          <span class="summary-pill">{{ t('newcomerGuide.memberOnly') }}</span>
          <span v-if="page?.updated_by" class="summary-pill">{{ t('newcomerGuide.updatedBy', { name: page.updated_by }) }}</span>
        </template>
        <template #actions>
          <button v-if="isStaff && !editing" class="button-box primary-action" type="button" @click="startEditing">
            <AppIcon name="edit" :size="16" />
            {{ t('newcomerGuide.edit') }}
          </button>
        </template>
      </PageHeader>

      <p v-if="loading" class="muted table-state">{{ t('newcomerGuide.loading') }}</p>
      <p v-if="error" class="error-text table-state">{{ error }}</p>
      <p v-if="success" class="success-text table-state">{{ success }}</p>

      <form v-if="editing && draft" class="newcomer-guide-editor" @submit.prevent="savePage">
        <section class="wire-section newcomer-editor-basics">
          <label class="input-panel embedded-field">
            <span>{{ t('newcomerGuide.editor.pageTitle') }}</span>
            <input v-model="draft.title" maxlength="180" required />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('newcomerGuide.editor.intro') }}</span>
            <textarea v-model="draft.intro" rows="4" maxlength="4000" />
          </label>
        </section>

        <section
          v-for="(block, blockIndex) in draft.blocks"
          :key="`block-${blockIndex}`"
          class="wire-section newcomer-editor-block"
        >
          <div class="workspace-section-heading compact-heading">
            <div>
              <p class="eyebrow">{{ t('newcomerGuide.editor.block', { index: blockIndex + 1 }) }}</p>
              <h2>{{ block.title || t('newcomerGuide.editor.untitled') }}</h2>
            </div>
            <div class="compact-actions">
              <button class="form-button secondary-action" type="button" :disabled="blockIndex === 0" @click="moveBlock(blockIndex, -1)">↑</button>
              <button class="form-button secondary-action" type="button" :disabled="blockIndex === draft.blocks.length - 1" @click="moveBlock(blockIndex, 1)">↓</button>
              <button class="form-button danger-action" type="button" @click="removeBlock(blockIndex)">{{ t('common.remove') }}</button>
            </div>
          </div>

          <div class="directory-form-grid newcomer-block-fields">
            <label class="input-panel embedded-field">
              <span>{{ t('newcomerGuide.editor.blockType') }}</span>
              <select v-model="block.block_type">
                <option value="text">{{ t('newcomerGuide.editor.textBlock') }}</option>
                <option value="resources">{{ t('newcomerGuide.editor.resourceBlock') }}</option>
              </select>
            </label>
            <label class="input-panel embedded-field">
              <span>{{ t('common.title') }}</span>
              <input v-model="block.title" maxlength="180" required />
            </label>
          </div>
          <div class="newcomer-markdown-field">
            <span class="field-label">{{ block.block_type === 'text' ? t('newcomerGuide.editor.text') : t('newcomerGuide.editor.optionalIntro') }}</span>
            <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
            <MarkdownEditor
              v-model="block.body"
              :rows="5"
              :maxlength="20000"
              :required="block.block_type === 'text'"
            />
          </div>

          <div v-if="block.block_type === 'resources'" class="newcomer-resource-editor-list">
            <p v-if="resourceOptionsLoading" class="muted section-helper-text">{{ t('newcomerGuide.editor.loadingResources') }}</p>
            <p v-else-if="resourceOptionsError" class="error-text section-helper-text">{{ resourceOptionsError }}</p>
            <article v-for="(resource, resourceIndex) in block.resources" :key="`resource-${resourceIndex}`" class="newcomer-resource-editor-row">
              <div class="newcomer-resource-editor-head">
                <strong>{{ t('newcomerGuide.editor.resource', { index: resourceIndex + 1 }) }}</strong>
                <div class="compact-actions">
                  <button type="button" :disabled="resourceIndex === 0" @click="moveResource(block, resourceIndex, -1)">↑</button>
                  <button type="button" :disabled="resourceIndex === block.resources.length - 1" @click="moveResource(block, resourceIndex, 1)">↓</button>
                  <button type="button" @click="removeResource(block, resourceIndex)">{{ t('common.remove') }}</button>
                </div>
              </div>
              <div class="directory-form-grid">
                <label class="input-panel embedded-field">
                  <span>{{ t('common.type') }}</span>
                  <select v-model="resource.resource_type" @change="onResourceTypeChange(resource)">
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
            <button class="form-button secondary-action" type="button" @click="addResource(block)">{{ t('newcomerGuide.editor.addResource') }}</button>
          </div>
        </section>

        <div class="newcomer-editor-add-row">
          <button class="form-button secondary-action" type="button" @click="addBlock('text')">{{ t('newcomerGuide.editor.addTextBlock') }}</button>
          <button class="form-button secondary-action" type="button" @click="addBlock('resources')">{{ t('newcomerGuide.editor.addResourceBlock') }}</button>
          <button class="form-button secondary-action" type="button" @click="addLinkedResource('guide')">{{ t('newcomerGuide.editor.linkGuide') }}</button>
          <button class="form-button secondary-action" type="button" @click="addLinkedResource('build')">{{ t('newcomerGuide.editor.linkBuild') }}</button>
        </div>
        <div class="form-actions">
          <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('common.saving') : t('common.save') }}</button>
          <button class="form-button secondary-action" type="button" @click="cancelEditing">{{ t('common.cancel') }}</button>
        </div>
      </form>

      <div v-else-if="page" class="newcomer-guide-content">
        <section
          v-for="(block, index) in page.blocks"
          :key="block.id"
          class="wire-section newcomer-guide-block"
          :class="`newcomer-guide-block--${block.block_type}`"
        >
          <div class="newcomer-guide-block-index">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="workspace-section-heading">
            <div>
              <p class="eyebrow">{{ block.block_type === 'text' ? t('newcomerGuide.textSection') : t('newcomerGuide.resourceSection') }}</p>
              <h2>{{ block.title }}</h2>
              <RichTextRenderer v-if="block.body" :body="block.body" />
            </div>
          </div>
          <div v-if="block.block_type === 'resources'" class="newcomer-resource-grid">
            <component
              :is="resourceComponent(resource)"
              v-for="resource in block.resources"
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
      </div>
    </div>
  </section>
</template>
