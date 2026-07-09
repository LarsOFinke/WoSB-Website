<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { useLocale } from '@/locales'
import { createThread } from '@/services/forum'

const router = useRouter()
const { t } = useLocale()
const saving = ref(false)
const error = ref('')
const attachments = ref([])

const categories = ['general', 'builds', 'events', 'support']
const form = reactive({ title: '', category: 'general', body: '' })
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value)

function addAttachment(file) {
  attachments.value.push(file)
}

function removeAttachment(fileId) {
  attachments.value = attachments.value.filter((file) => file.id !== fileId)
}

async function submitThread() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  try {
    const created = await createThread({
      title: form.title,
      category: form.category,
      body: form.body,
      file_ids: attachments.value.map((file) => file.id),
    })
    await router.push(`/forum/${created.id}`)
  } catch (err) {
    error.value = err.message || t('forum.create.saveError')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="forum-create-page" aria-labelledby="forum-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean forum-create-frame" @submit.prevent="submitThread">
      <div class="create-topline">
        <RouterLink class="small-action" to="/forum">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.forum') }}</p>
          <h1 id="forum-create-title">{{ t('forum.create.title') }}</h1>
          <p>{{ t('forum.create.subtitle') }}</p>
        </div>
      </div>

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

      <section class="wire-section form-section">
        <div class="section-title"><span>02</span><h2>{{ t('forum.create.sections.body') }}</h2></div>
        <label class="input-panel embedded-field textarea-shell">
          <textarea v-model="form.body" rows="8" maxlength="8000" :placeholder="t('forum.create.bodyPlaceholder')"></textarea>
        </label>
      </section>

      <section class="wire-section form-section">
        <div class="section-title"><span>03</span><h2>{{ t('files.attachments') }}</h2></div>
        <FileUploadPanel usage-context="forum" @uploaded="addAttachment" />
        <AttachmentGallery :attachments="attachments" />
        <div v-if="attachments.length" class="attachment-chip-row">
          <button v-for="file in attachments" :key="file.id" class="chip-remove" type="button" @click="removeAttachment(file.id)">× {{ file.original_name }}</button>
        </div>
      </section>

      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div class="form-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving ? t('forum.create.saving') : t('forum.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
