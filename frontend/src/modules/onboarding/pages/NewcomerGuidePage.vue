<script setup>
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listBuilds } from '@/modules/builds/api/builds'
import { listGuides } from '@/modules/guides/api/guides'
import { getNewcomerGuide, updateNewcomerGuide } from '@/modules/onboarding/api/newcomerGuide'
import { appendLinkedResource } from '@/modules/onboarding/services/newcomerGuideResources'

const { t } = useLocale()
const { isStaff } = useSession()
const page = ref(null)
const draft = ref(null)
const guides = ref([])
const builds = ref([])
const loading = ref(false)
const saving = ref(false)
const editing = ref(false)
const error = ref('')
const success = ref('')
const resourceOptionsLoading = ref(false)
const resourceOptionsLoaded = ref(false)
const resourceOptionsError = ref('')

const resourceTypeOptions = computed(() => [
  { value: 'guide', label: t('newcomerGuide.editor.types.guide') },
  { value: 'build', label: t('newcomerGuide.editor.types.build') },
  { value: 'internal', label: t('newcomerGuide.editor.types.internal') },
  { value: 'external', label: t('newcomerGuide.editor.types.external') },
])

function emptyTextBlock() {
  return { block_type: 'text', title: '', body: '', resources: [] }
}

function emptyResourceBlock() {
  return { block_type: 'resources', title: '', body: '', resources: [] }
}

function emptyResource() {
  return { resource_type: 'guide', resource_id: null, label: '', description: '', url: '' }
}

function toDraft(source) {
  return {
    title: source.title,
    intro: source.intro,
    blocks: (source.blocks || []).map((block) => ({
      block_type: block.block_type,
      title: block.title,
      body: block.body || '',
      resources: (block.resources || []).map((resource) => ({
        resource_type: resource.resource_type,
        resource_id: resource.resource_id || null,
        label: resource.label || '',
        description: resource.description || '',
        url: ['internal', 'external'].includes(resource.resource_type) ? resource.href : '',
      })),
    })),
  }
}

function normalizePayload() {
  return {
    title: draft.value.title,
    intro: draft.value.intro,
    blocks: draft.value.blocks.map((block) => ({
      block_type: block.block_type,
      title: block.title,
      body: block.body || null,
      resources: block.block_type === 'resources'
        ? block.resources.map((resource) => ({
            resource_type: resource.resource_type,
            resource_id: ['guide', 'build'].includes(resource.resource_type) ? Number(resource.resource_id) : null,
            label: resource.label || null,
            description: resource.description || null,
            url: ['internal', 'external'].includes(resource.resource_type) ? resource.url : null,
          }))
        : [],
    })),
  }
}

function resourceComponent(resource) {
  return resource.resource_type === 'external' ? 'a' : 'RouterLink'
}

function resourceTarget(resource) {
  return resource.resource_type === 'external'
    ? { href: resource.href, target: '_blank', rel: 'noopener' }
    : { to: resource.href }
}

async function loadResourceOptions() {
  if (resourceOptionsLoaded.value || resourceOptionsLoading.value) return
  resourceOptionsLoading.value = true
  resourceOptionsError.value = ''
  try {
    const [guideRows, buildRows] = await Promise.all([listGuides(), listBuilds()])
    guides.value = guideRows
    builds.value = buildRows
    resourceOptionsLoaded.value = true
  } catch (err) {
    resourceOptionsError.value = err.message || t('newcomerGuide.editor.resourceLoadError')
  } finally {
    resourceOptionsLoading.value = false
  }
}

async function startEditing() {
  draft.value = toDraft(page.value)
  editing.value = true
  success.value = ''
  await loadResourceOptions()
}

function cancelEditing() {
  editing.value = false
  draft.value = null
  error.value = ''
}

function addBlock(type) {
  draft.value.blocks.push(type === 'resources' ? emptyResourceBlock() : emptyTextBlock())
}

function removeBlock(index) {
  draft.value.blocks.splice(index, 1)
}

function moveBlock(index, delta) {
  const target = index + delta
  if (target < 0 || target >= draft.value.blocks.length) return
  const [block] = draft.value.blocks.splice(index, 1)
  draft.value.blocks.splice(target, 0, block)
}

function addResource(block) {
  block.resources.push(emptyResource())
}

function addLinkedResource(resourceType) {
  const block = appendLinkedResource(draft.value.blocks, resourceType)
  if (block) {
    if (!block.title) block.title = t('newcomerGuide.resourceSection')
    const row = block.resources.at(-1)
    row.resource_id = null
  }
}

function removeResource(block, index) {
  block.resources.splice(index, 1)
}

function moveResource(block, index, delta) {
  const target = index + delta
  if (target < 0 || target >= block.resources.length) return
  const [resource] = block.resources.splice(index, 1)
  block.resources.splice(target, 0, resource)
}

function onResourceTypeChange(resource) {
  resource.resource_id = null
  resource.url = ''
}

async function loadPage() {
  loading.value = true
  error.value = ''
  try {
    page.value = await getNewcomerGuide()
  } catch (err) {
    error.value = err.message || t('newcomerGuide.loadError')
  } finally {
    loading.value = false
  }
}

async function savePage() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    page.value = await updateNewcomerGuide(normalizePayload())
    editing.value = false
    draft.value = null
    success.value = t('newcomerGuide.saved')
  } catch (err) {
    error.value = err.message || t('newcomerGuide.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(loadPage)
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
