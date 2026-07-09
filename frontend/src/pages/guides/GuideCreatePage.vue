<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { useLocale } from '@/locales'
import { createGuide } from '@/services/guides'

const router = useRouter()
const { t } = useLocale()
const saving = ref(false)
const error = ref('')
const attachments = ref([])
const categories = ['general', 'builds', 'combat', 'economy']
const form = reactive({ title: '', category: 'general', summary: '', body: '' })
const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value)

function addAttachment(file) {
  attachments.value.push(file)
}

function removeAttachment(fileId) {
  attachments.value = attachments.value.filter((file) => file.id !== fileId)
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

      <section class="wire-section form-section">
        <div class="section-title"><span>02</span><h2>{{ t('guides.create.sections.body') }}</h2></div>
        <label class="input-panel embedded-field textarea-shell">
          <textarea v-model="form.body" rows="12" maxlength="20000" :placeholder="t('guides.create.bodyPlaceholder')"></textarea>
        </label>
      </section>

      <section class="wire-section form-section">
        <div class="section-title"><span>03</span><h2>{{ t('files.attachments') }}</h2></div>
        <FileUploadPanel usage-context="guide" @uploaded="addAttachment" />
        <AttachmentGallery :attachments="attachments" />
        <div v-if="attachments.length" class="attachment-chip-row">
          <button v-for="file in attachments" :key="file.id" class="chip-remove" type="button" @click="removeAttachment(file.id)">× {{ file.original_name }}</button>
        </div>
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
