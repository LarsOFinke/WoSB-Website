<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import BuildInsertPanel from '@/core/components/BuildInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import LinkedBuildList from '@/core/components/LinkedBuildList.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'
import { createGuide, getGuide, updateGuide } from '@/modules/guides/api/guides'
import { createBuildEmbedToken, createEmbedToken, removeBuildEmbedTokens, removeFileEmbedTokens, unembeddedAttachments, unembeddedBuilds } from '@/shared/content/richTextEmbeds'

const route = useRoute()
const router = useRouter()
const { t } = useLocale()
const saving = ref(false)
const loading = ref(false)
const loadingBuilds = ref(false)
const error = ref('')
const attachments = ref([])
const availableBuilds = ref([])
const linkedBuilds = ref([])
const bodyEditor = ref(null)
const categories = ['general', 'builds', 'combat', 'economy']
const form = reactive({ title: '', category: 'general', summary: '', body: '' })
const guideId = computed(() => route.params.id ? Number(route.params.id) : null)
const isEditing = computed(() => Number.isInteger(guideId.value) && guideId.value > 0)
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value && !loading.value)
const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
const linkedBuildCards = computed(() => unembeddedBuilds(linkedBuilds.value, form.body))
const hasPreview = computed(() => form.body.trim() || attachments.value.length || linkedBuilds.value.length)
const backTarget = computed(() => isEditing.value ? `/guides/${guideId.value}` : '/guides')

function addAttachment(file) {
  if (!attachments.value.some((item) => item.id === file.id)) {
    attachments.value.push(file)
  }
}

function removeAttachment(fileId) {
  attachments.value = attachments.value.filter((file) => file.id !== fileId)
  form.body = removeFileEmbedTokens(form.body, fileId)
}

function addBuildReference(build) {
  if (!build || linkedBuilds.value.some((item) => Number(item.id) === Number(build.id))) return
  linkedBuilds.value.push(build)
}

function removeBuildReference(buildId) {
  linkedBuilds.value = linkedBuilds.value.filter((build) => Number(build.id) !== Number(buildId))
  form.body = removeBuildEmbedTokens(form.body, buildId)
}

async function insertTextToken(token) {
  if (bodyEditor.value?.insertToken) {
    await bodyEditor.value.insertToken(token)
    return
  }
  form.body = `${form.body}${form.body.endsWith('\n') || !form.body ? '' : '\n\n'}${token}\n\n`
}

async function insertAttachment({ file, size }) {
  await insertTextToken(createEmbedToken(file.id, size))
}

async function insertBuild({ build, layout }) {
  addBuildReference(build)
  await insertTextToken(createBuildEmbedToken(build.id, layout))
}

async function loadBuildCatalog() {
  loadingBuilds.value = true
  try {
    availableBuilds.value = await listBuilds('', '')
  } catch (err) {
    error.value = err.message || t('buildEmbeds.loadError')
  } finally {
    loadingBuilds.value = false
  }
}

async function loadGuideForEditing() {
  if (!isEditing.value) return
  loading.value = true
  error.value = ''
  try {
    const guide = await getGuide(guideId.value)
    form.title = guide.title
    form.category = guide.category
    form.summary = guide.summary || ''
    form.body = guide.body
    attachments.value = [...(guide.attachments || [])]
    linkedBuilds.value = [...(guide.builds || [])]
  } catch (err) {
    error.value = err.message || t('guides.edit.loadError')
  } finally {
    loading.value = false
  }
}

async function submitGuide() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  const payload = {
    title: form.title,
    category: form.category,
    summary: form.summary || null,
    body: form.body,
    file_ids: attachments.value.map((file) => file.id),
    build_ids: linkedBuilds.value.map((build) => build.id),
  }
  try {
    const saved = isEditing.value
      ? await updateGuide(guideId.value, payload)
      : await createGuide(payload)
    await router.push(`/guides/${saved.id}`)
  } catch (err) {
    error.value = err.message || t(isEditing.value ? 'guides.edit.saveError' : 'guides.create.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadBuildCatalog(), loadGuideForEditing()])
})
</script>

<template>
  <section class="guide-create-page" aria-labelledby="guide-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean guide-create-frame" @submit.prevent="submitGuide">
      <div class="create-topline">
        <RouterLink class="small-action" :to="backTarget">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.guides') }}</p>
          <h1 id="guide-create-title">{{ t(isEditing ? 'guides.edit.title' : 'guides.create.title') }}</h1>
          <p>{{ t(isEditing ? 'guides.edit.subtitle' : 'guides.create.subtitle') }}</p>
        </div>
      </div>

      <p v-if="loading" class="wire-section muted">{{ t('guides.edit.loading') }}</p>

      <template v-else>
        <section class="wire-section form-section">
          <div class="section-title"><span>01</span><h2>{{ t('guides.create.sections.basics') }}</h2></div>
          <div class="section-fields two-fields">
            <label class="input-panel embedded-field">
              <input v-model="form.title" required maxlength="180" :placeholder="t('guides.create.titlePlaceholder')" />
            </label>
            <label class="select-shell full-select-shell">
              <select v-model="form.category">
                <option v-for="category in categories" :key="category" :value="category">{{ t(`guides.categories.${category}`) }}</option>
              </select>
            </label>
          </div>
          <label class="input-panel embedded-field textarea-shell">
            <textarea v-model="form.summary" rows="3" maxlength="400" :placeholder="t('guides.create.summaryPlaceholder')"></textarea>
          </label>
        </section>

        <section class="wire-section form-section rich-editor-section">
          <div class="section-title"><span>02</span><h2>{{ t('guides.create.sections.body') }}</h2></div>
          <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
          <MarkdownEditor
            ref="bodyEditor"
            v-model="form.body"
            :rows="14"
            :maxlength="20000"
            :placeholder="t('guides.create.bodyPlaceholder')"
            required
          />
        </section>

        <section class="wire-section form-section">
          <div class="section-title"><span>03</span><h2>{{ t('buildEmbeds.sectionTitle') }}</h2></div>
          <p class="section-helper-text">{{ t('buildEmbeds.sectionHint') }}</p>
          <BuildInsertPanel
            :builds="availableBuilds"
            :linked-builds="linkedBuilds"
            :loading="loadingBuilds"
            @link="addBuildReference"
            @unlink="removeBuildReference"
            @insert="insertBuild"
          />
        </section>

        <section class="wire-section form-section">
          <div class="section-title"><span>04</span><h2>{{ t('files.attachments') }}</h2></div>
          <FileUploadPanel usage-context="guide" @uploaded="addAttachment" />
          <AttachmentInsertPanel :attachments="attachments" @insert="insertAttachment" @remove="removeAttachment" />
          <AttachmentGallery :attachments="galleryAttachments" />
        </section>

        <section v-if="hasPreview" class="wire-section form-section rich-preview-section">
          <div class="section-title"><span>05</span><h2>{{ t('files.previewTitle') }}</h2></div>
          <p v-if="form.summary" class="guide-summary">{{ form.summary }}</p>
          <RichTextRenderer :body="form.body" :attachments="attachments" :builds="linkedBuilds" />
          <LinkedBuildList :builds="linkedBuildCards" />
          <AttachmentGallery :attachments="galleryAttachments" />
        </section>
      </template>

      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div v-if="!loading" class="form-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving
            ? t(isEditing ? 'guides.edit.saving' : 'guides.create.saving')
            : t(isEditing ? 'guides.edit.save' : 'guides.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
