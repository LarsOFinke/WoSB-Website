<script setup>
import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useForumCreatePage } from '@/modules/forum/composables/useForumCreatePage'

const {
  route,
  router,
  t,
  saving,
  loading,
  error,
  attachments,
  bodyEditor,
  categories,
  form,
  threadId,
  isEditing,
  canSubmit,
  galleryAttachments,
  hasPreview,
  backTarget,
  addAttachment,
  removeAttachment,
  insertAttachment,
  loadThreadForEditing,
  submitThread,
  createEmbedToken,
  removeFileEmbedTokens,
  unembeddedAttachments,
} = useForumCreatePage()
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
