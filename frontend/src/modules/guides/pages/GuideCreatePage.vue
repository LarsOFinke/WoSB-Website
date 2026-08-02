<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import BuildInsertPanel from '@/core/components/BuildInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import LinkedBuildList from '@/core/components/LinkedBuildList.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import '@/modules/guides/styles/guideFoundation.css'
import '@/modules/guides/styles/guideEditor.css'
import '@/modules/guides/styles/guideResponsive.css'
import { useGuideCreatePage } from '@/modules/guides/composables/useGuideCreatePage'

const {
  route,
  router,
  t,
  saving,
  loading,
  loadingBuilds,
  error,
  attachments,
  availableBuilds,
  linkedBuilds,
  bodyEditor,
  form,
  categories,
  guideId,
  isEditing,
  canSubmit,
  galleryAttachments,
  linkedBuildCards,
  hasPreview,
  backTarget,
  addAttachment,
  removeAttachment,
  addBuildReference,
  removeBuildReference,
  insertTextToken,
  insertAttachment,
  insertBuild,
  loadBuildCatalog,
  loadGuideForEditing,
  submitGuide,
  localizedGuideCategoryItems,
  createBuildEmbedToken,
  createEmbedToken,
  removeBuildEmbedTokens,
  removeFileEmbedTokens,
  unembeddedAttachments,
  unembeddedBuilds,
} = useGuideCreatePage()
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
