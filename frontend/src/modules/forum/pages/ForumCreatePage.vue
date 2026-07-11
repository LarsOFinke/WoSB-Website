<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { createThread, getThread, updateThread } from '@/modules/forum/api/forum'
import { createEmbedToken, removeFileEmbedTokens, unembeddedAttachments } from '@/shared/content/richTextEmbeds'

const route = useRoute()
const router = useRouter()
const { t } = useLocale()
const saving = ref(false)
const loading = ref(false)
const error = ref('')
const attachments = ref([])
const bodyEditor = ref(null)

const categories = ['general', 'builds', 'events', 'support', 'training', 'logistics']
const form = reactive({ title: '', category: 'general', body: '' })
const threadId = computed(() => route.params.id ? Number(route.params.id) : null)
const isEditing = computed(() => Number.isInteger(threadId.value) && threadId.value > 0)
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value && !loading.value)
const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
const hasPreview = computed(() => form.body.trim() || attachments.value.length)
const backTarget = computed(() => isEditing.value ? `/forum/${threadId.value}` : '/forum')

function addAttachment(file) {
  if (!attachments.value.some((item) => item.id === file.id)) {
    attachments.value.push(file)
  }
}

function removeAttachment(fileId) {
  attachments.value = attachments.value.filter((file) => file.id !== fileId)
  form.body = removeFileEmbedTokens(form.body, fileId)
}

async function insertAttachment({ file, size }) {
  const token = createEmbedToken(file.id, size)
  if (bodyEditor.value?.insertToken) {
    await bodyEditor.value.insertToken(token)
    return
  }
  form.body = `${form.body}${form.body.endsWith('\n') || !form.body ? '' : '\n\n'}${token}\n\n`
}

async function loadThreadForEditing() {
  if (!isEditing.value) return
  loading.value = true
  error.value = ''
  try {
    const thread = await getThread(threadId.value)
    const openingPost = thread.posts?.[0]
    form.title = thread.title
    form.category = thread.category
    form.body = openingPost?.body || ''
    attachments.value = [...(openingPost?.attachments || [])]
  } catch (err) {
    error.value = err.message || t('forum.edit.loadError')
  } finally {
    loading.value = false
  }
}

async function submitThread() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  const payload = {
    title: form.title,
    category: form.category,
    body: form.body,
    file_ids: attachments.value.map((file) => file.id),
  }
  try {
    const saved = isEditing.value
      ? await updateThread(threadId.value, payload)
      : await createThread(payload)
    await router.push(`/forum/${saved.id}`)
  } catch (err) {
    error.value = err.message || t(isEditing.value ? 'forum.edit.saveError' : 'forum.create.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(loadThreadForEditing)
</script>

<template>
  <section class="forum-create-page" aria-labelledby="forum-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean forum-create-frame" @submit.prevent="submitThread">
      <div class="create-topline">
        <RouterLink class="small-action" :to="backTarget">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.forum') }}</p>
          <h1 id="forum-create-title">{{ t(isEditing ? 'forum.edit.title' : 'forum.create.title') }}</h1>
          <p>{{ t(isEditing ? 'forum.edit.subtitle' : 'forum.create.subtitle') }}</p>
        </div>
      </div>

      <p v-if="loading" class="wire-section muted">{{ t('forum.edit.loading') }}</p>

      <template v-else>
        <section class="wire-section form-section">
          <div class="section-title"><span>01</span><h2>{{ t('forum.create.sections.thread') }}</h2></div>
          <div class="section-fields two-fields">
            <label class="input-panel embedded-field">
              <input v-model="form.title" required maxlength="160" :placeholder="t('forum.create.titlePlaceholder')" />
            </label>
            <label class="select-shell full-select-shell">
              <select v-model="form.category">
                <option v-for="category in categories" :key="category" :value="category">{{ t(`forum.categories.${category}`) }}</option>
              </select>
            </label>
          </div>
        </section>

        <section class="wire-section form-section rich-editor-section">
          <div class="section-title"><span>02</span><h2>{{ t('forum.create.sections.body') }}</h2></div>
          <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
          <MarkdownEditor
            ref="bodyEditor"
            v-model="form.body"
            :rows="10"
            :maxlength="8000"
            :placeholder="t('forum.create.bodyPlaceholder')"
            required
          />
        </section>

        <section class="wire-section form-section">
          <div class="section-title"><span>03</span><h2>{{ t('files.attachments') }}</h2></div>
          <FileUploadPanel usage-context="forum" @uploaded="addAttachment" />
          <AttachmentInsertPanel :attachments="attachments" @insert="insertAttachment" @remove="removeAttachment" />
          <AttachmentGallery :attachments="galleryAttachments" />
        </section>

        <section v-if="hasPreview" class="wire-section form-section rich-preview-section">
          <div class="section-title"><span>04</span><h2>{{ t('files.previewTitle') }}</h2></div>
          <RichTextRenderer :body="form.body" :attachments="attachments" />
          <AttachmentGallery :attachments="galleryAttachments" />
        </section>
      </template>

      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div v-if="!loading" class="form-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving
            ? t(isEditing ? 'forum.edit.saving' : 'forum.create.saving')
            : t(isEditing ? 'forum.edit.save' : 'forum.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
