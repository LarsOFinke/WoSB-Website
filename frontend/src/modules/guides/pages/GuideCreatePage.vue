<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/core/components/AppIcon.vue'
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
import { localizedGuideCategoryItems } from '@/modules/guides/domain/guideDiscovery'
import '@/modules/guides/styles/guides.css'
import {
  createBuildEmbedToken,
  createEmbedToken,
  removeBuildEmbedTokens,
  removeFileEmbedTokens,
  unembeddedAttachments,
  unembeddedBuilds,
} from '@/shared/content/richTextEmbeds'

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
const form = reactive({ title: '', category: 'general', summary: '', body: '' })

const categories = computed(() => localizedGuideCategoryItems(t))
const guideId = computed(() => route.params.id ? Number(route.params.id) : null)
const isEditing = computed(() => Number.isInteger(guideId.value) && guideId.value > 0)
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value && !loading.value)
const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
const linkedBuildCards = computed(() => unembeddedBuilds(linkedBuilds.value, form.body))
const hasPreview = computed(() => form.body.trim() || attachments.value.length || linkedBuilds.value.length)
const backTarget = computed(() => isEditing.value ? `/guides/${guideId.value}` : '/guides')

function addAttachment(file) {
  if (!attachments.value.some((item) => item.id === file.id)) attachments.value.push(file)
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
  <section class="guide-editor-page" aria-labelledby="guide-create-title">
    <form class="guide-module-frame guide-editor-frame" @submit.prevent="submitGuide">
      <header class="guide-editor-commandbar">
        <RouterLink class="guide-back-action" :to="backTarget">
          <AppIcon name="chevron-left" :size="18" />
          {{ t('common.back') }}
        </RouterLink>
        <h1 id="guide-create-title">{{ t(isEditing ? 'guides.edit.title' : 'guides.create.title') }}</h1>
        <button class="guide-primary-action is-compact" type="submit" :disabled="!canSubmit">
          {{ saving
            ? t(isEditing ? 'guides.edit.saving' : 'guides.create.saving')
            : t(isEditing ? 'guides.edit.save' : 'guides.create.save') }}
        </button>
      </header>

      <p v-if="loading" class="guide-state-message">{{ t('guides.edit.loading') }}</p>
      <p v-if="error" class="guide-inline-status error-text">{{ error }}</p>

      <template v-if="!loading">
        <section class="guide-editor-meta" :aria-label="t('guides.create.sections.basics')">
          <label class="guide-editor-field is-title">
            <span>{{ t('guides.create.titlePlaceholder') }}</span>
            <input v-model="form.title" required maxlength="180" :placeholder="t('guides.create.titlePlaceholder')" />
          </label>
          <label class="guide-editor-field is-category">
            <span>{{ t('discovery.guides.formTitle') }}</span>
            <select v-model="form.category">
              <option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <label class="guide-editor-field is-summary">
            <span>{{ t('guides.create.summaryPlaceholder') }}</span>
            <textarea v-model="form.summary" rows="2" maxlength="400" :placeholder="t('guides.create.summaryPlaceholder')"></textarea>
          </label>
        </section>

        <div class="guide-editor-workspace">
          <main class="guide-writing-column">
            <section class="guide-writing-panel">
              <header>
                <h2>{{ t('guides.create.sections.body') }}</h2>
                <p>{{ t('markdown.editorHint') }}</p>
              </header>
              <MarkdownEditor
                ref="bodyEditor"
                v-model="form.body"
                :rows="22"
                :maxlength="20000"
                :placeholder="t('guides.create.bodyPlaceholder')"
                required
              />
            </section>

            <details v-if="hasPreview" class="guide-editor-disclosure guide-preview-disclosure">
              <summary>{{ t('files.previewTitle') }}</summary>
              <div class="guide-editor-preview">
                <p v-if="form.summary" class="guide-summary">{{ form.summary }}</p>
                <RichTextRenderer :body="form.body" :attachments="attachments" :builds="linkedBuilds" />
                <LinkedBuildList :builds="linkedBuildCards" />
                <AttachmentGallery :attachments="galleryAttachments" />
              </div>
            </details>
          </main>

          <aside class="guide-resource-rail">
            <details class="guide-editor-disclosure" open>
              <summary>{{ t('buildEmbeds.sectionTitle') }}</summary>
              <div class="guide-resource-content">
                <p>{{ t('buildEmbeds.sectionHint') }}</p>
                <BuildInsertPanel
                  :builds="availableBuilds"
                  :linked-builds="linkedBuilds"
                  :loading="loadingBuilds"
                  @link="addBuildReference"
                  @unlink="removeBuildReference"
                  @insert="insertBuild"
                />
              </div>
            </details>

            <details class="guide-editor-disclosure" open>
              <summary>{{ t('files.attachments') }}</summary>
              <div class="guide-resource-content">
                <FileUploadPanel usage-context="guide" @uploaded="addAttachment" />
                <AttachmentInsertPanel
                  :attachments="attachments"
                  @insert="insertAttachment"
                  @remove="removeAttachment"
                />
              </div>
            </details>
          </aside>
        </div>
      </template>
    </form>
  </section>
</template>
