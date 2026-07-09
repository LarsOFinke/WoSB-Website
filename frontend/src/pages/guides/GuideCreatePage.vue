<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { createGuide } from '@/services/guides'
import { createEmbedToken, unembeddedAttachments } from '@/services/richTextEmbeds'

const router = useRouter()
const { t } = useLocale()
const saving = ref(false)
const error = ref('')
const attachments = ref([])
const bodyInput = ref(null)
const categories = ['general', 'builds', 'combat', 'economy']
const form = reactive({ title: '', category: 'general', summary: '', body: '' })
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value)
const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
const hasPreview = computed(() => form.body.trim() || attachments.value.length)

function addAttachment(file) {
  if (!attachments.value.some((item) => item.id === file.id)) {
    attachments.value.push(file)
  }
}

function removeAttachment(fileId) {
  attachments.value = attachments.value.filter((file) => file.id !== fileId)
}

async function insertAttachment({ file, size }) {
  const token = createEmbedToken(file.id, size)
  const input = bodyInput.value
  if (!input) {
    form.body = `${form.body}${form.body.endsWith('\n') || !form.body ? '' : '\n\n'}${token}\n\n`
    return
  }

  const start = input.selectionStart ?? form.body.length
  const end = input.selectionEnd ?? form.body.length
  const before = form.body.slice(0, start)
  const after = form.body.slice(end)
  const paddedToken = `${before && !before.endsWith('\n') ? '\n\n' : ''}${token}${after && !after.startsWith('\n') ? '\n\n' : ''}`
  form.body = `${before}${paddedToken}${after}`
  await nextTick()
  const cursorPosition = before.length + paddedToken.length
  input.focus()
  input.setSelectionRange(cursorPosition, cursorPosition)
}

async function submitGuide() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  try {
    const created = await createGuide({
      title: form.title,
      category: form.category,
      summary: form.summary || null,
      body: form.body,
      file_ids: attachments.value.map((file) => file.id),
    })
    await router.push(`/guides/${created.id}`)
  } catch (err) {
    error.value = err.message || t('guides.create.saveError')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="guide-create-page" aria-labelledby="guide-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean guide-create-frame" @submit.prevent="submitGuide">
      <div class="create-topline">
        <RouterLink class="small-action" to="/guides">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.guides') }}</p>
          <h1 id="guide-create-title">{{ t('guides.create.title') }}</h1>
          <p>{{ t('guides.create.subtitle') }}</p>
        </div>
      </div>

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
        <p class="section-helper-text">{{ t('files.inlineEditorHint') }}</p>
        <label class="input-panel embedded-field textarea-shell">
          <textarea ref="bodyInput" v-model="form.body" rows="14" maxlength="20000" :placeholder="t('guides.create.bodyPlaceholder')"></textarea>
        </label>
      </section>

      <section class="wire-section form-section">
        <div class="section-title"><span>03</span><h2>{{ t('files.attachments') }}</h2></div>
        <FileUploadPanel usage-context="guide" @uploaded="addAttachment" />
        <AttachmentInsertPanel :attachments="attachments" @insert="insertAttachment" @remove="removeAttachment" />
        <AttachmentGallery :attachments="galleryAttachments" />
      </section>

      <section v-if="hasPreview" class="wire-section form-section rich-preview-section">
        <div class="section-title"><span>04</span><h2>{{ t('files.previewTitle') }}</h2></div>
        <p v-if="form.summary" class="guide-summary">{{ form.summary }}</p>
        <RichTextRenderer :body="form.body" :attachments="attachments" />
        <AttachmentGallery :attachments="galleryAttachments" />
      </section>

      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div class="form-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving ? t('guides.create.saving') : t('guides.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
