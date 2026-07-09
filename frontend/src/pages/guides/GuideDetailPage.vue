<script setup>
import { computed, onMounted, ref } from 'vue'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import { useLocale } from '@/locales'
import { deleteGuide, getGuide } from '@/services/guides'
import { useSession } from '@/services/session'

const props = defineProps({ id: { type: String, required: true } })
const { t } = useLocale()
const { isStaff, user } = useSession()
const guide = ref(null)
const loading = ref(false)
const deleting = ref(false)
const error = ref('')

const canManage = computed(() => guide.value && user.value && (guide.value.owner_id === user.value.id || isStaff.value))

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

async function loadGuide() {
  loading.value = true
  error.value = ''
  try {
    guide.value = await getGuide(props.id)
  } catch (err) {
    error.value = err.message || t('guides.detail.loadError')
  } finally {
    loading.value = false
  }
}

async function submitDelete() {
  if (!guide.value || !window.confirm(t('guides.detail.confirmDelete'))) return
  deleting.value = true
  error.value = ''
  try {
    await deleteGuide(guide.value.id)
    window.location.href = '/guides'
  } catch (err) {
    error.value = err.message || t('guides.detail.deleteError')
  } finally {
    deleting.value = false
  }
}

onMounted(loadGuide)
</script>

<template>
  <section class="guide-detail-page" aria-labelledby="guide-detail-title">
    <div class="wire-frame page-frame detail-frame guide-detail-frame">
      <header class="wire-section detail-header guide-detail-header">
        <RouterLink class="small-action" to="/guides">{{ t('common.back') }}</RouterLink>
        <div v-if="guide">
          <p class="eyebrow">{{ t(`guides.categories.${guide.category}`) }}</p>
          <h1 id="guide-detail-title">{{ guide.title }}</h1>
          <p>{{ t('guides.detail.meta', { name: guide.owner.display_name, value: formatDate(guide.created_at) }) }}</p>
        </div>
      </header>

      <p v-if="loading" class="wire-section muted">{{ t('guides.detail.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text">{{ error }}</p>

      <template v-else-if="guide">
        <article class="wire-section guide-content-card">
          <p v-if="guide.summary" class="guide-summary">{{ guide.summary }}</p>
          <p class="preserve-lines">{{ guide.body }}</p>
          <AttachmentGallery :attachments="guide.attachments" />
        </article>

        <section v-if="canManage" class="wire-section guide-management-panel">
          <p class="eyebrow">{{ t('guides.detail.manageEyebrow') }}</p>
          <button class="danger-action" type="button" :disabled="deleting" @click="submitDelete">
            {{ deleting ? t('guides.detail.deleting') : t('guides.detail.delete') }}
          </button>
        </section>
      </template>
    </div>
  </section>
</template>
