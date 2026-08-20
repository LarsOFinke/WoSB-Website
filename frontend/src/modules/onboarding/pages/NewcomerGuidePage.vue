<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import NewcomerFolderEditor from '@/modules/onboarding/components/NewcomerFolderEditor.vue'
import NewcomerFolderNavigation from '@/modules/onboarding/components/NewcomerFolderNavigation.vue'
import NewcomerTopicExplorer from '@/modules/onboarding/components/NewcomerTopicExplorer.vue'
import { useNewcomerGuidePage } from '@/modules/onboarding/composables/useNewcomerGuidePage.js'
import '@/modules/onboarding/styles/newcomerEditor.css'
import '@/modules/onboarding/styles/newcomerExplorer.css'

const {
  t, isStaff, page, draft, guides, builds, loading, saving, editing, error, success,
  resourceOptionsLoading, resourceOptionsError, resourceTypeOptions,
  activeFolderIndex, activeFolder, visibleFolders, startEditing, cancelEditing,
  addBlock, removeBlock, moveBlock, addResource, removeResource,
  moveResource, onResourceTypeChange, savePage, selectFolder,
  showTopicOverview,
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
        <header class="newcomer-editor-commandbar">
          <div>
            <p class="eyebrow">{{ t('newcomerGuide.editor.guideSettings') }}</p>
            <h2>{{ draft.title || t('newcomerGuide.title') }}</h2>
            <p>{{ t('newcomerGuide.editor.saveHint') }}</p>
          </div>
          <div class="newcomer-editor-commandbar__actions">
            <button class="form-button secondary-action" type="button" @click="cancelEditing">{{ t('common.cancel') }}</button>
            <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('common.saving') : t('common.save') }}</button>
          </div>
        </header>

        <details class="newcomer-editor-basics" open>
          <summary>
            <span><AppIcon name="guides" :size="18" /></span>
            <span><strong>{{ t('newcomerGuide.editor.guideIdentity') }}</strong><small>{{ t('newcomerGuide.editor.guideSettings') }}</small></span>
          </summary>
          <div class="directory-form-grid">
            <label class="input-panel embedded-field">
              <span>{{ t('newcomerGuide.editor.pageTitle') }}</span>
              <input v-model="draft.title" maxlength="180" required />
            </label>
            <label class="input-panel embedded-field">
              <span>{{ t('newcomerGuide.editor.intro') }}</span>
              <textarea v-model="draft.intro" rows="3" maxlength="4000" />
            </label>
          </div>
        </details>

        <div class="newcomer-editor-workspace">
          <aside class="newcomer-editor-structure">
            <div class="newcomer-editor-structure__heading">
              <span><AppIcon name="folder" :size="18" /></span>
              <div><strong>{{ t('newcomerGuide.folders') }}</strong><small>{{ t('newcomerGuide.editor.orderHint') }}</small></div>
            </div>
            <NewcomerFolderNavigation
              :folders="visibleFolders" :active-index="activeFolderIndex" editable
              @select="selectFolder" @move="moveBlock" @remove="removeBlock"
            />
            <div class="newcomer-folder-create">
              <p class="field-label">{{ t('newcomerGuide.editor.addFolder') }}</p>
              <button class="form-button secondary-action" type="button" @click="addBlock('text')">+ {{ t('newcomerGuide.editor.addTextBlock') }}</button>
              <button class="form-button secondary-action" type="button" @click="addBlock('resources')">+ {{ t('newcomerGuide.editor.addResourceBlock') }}</button>
            </div>
          </aside>

          <NewcomerFolderEditor
            :folder="activeFolder" :folder-index="activeFolderIndex" :guides="guides" :builds="builds"
            :resource-type-options="resourceTypeOptions" :resource-options-loading="resourceOptionsLoading"
            :resource-options-error="resourceOptionsError" @add-resource="addResource"
            @remove-resource="removeResource" @move-resource="moveResource"
            @resource-type-change="onResourceTypeChange"
          />
        </div>
      </form>

      <div v-else-if="page" class="newcomer-guide-content">
        <NewcomerTopicExplorer
          :title="page.title"
          :intro="page.intro"
          :folders="visibleFolders"
          :active-index="activeFolderIndex"
          @home="showTopicOverview"
          @select="selectFolder"
        />
      </div>
    </div>
  </section>
</template>
