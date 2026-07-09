<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { useLocale } from '@/locales'
import { createPost, getThread } from '@/services/forum'
import { useSession } from '@/services/session'

const props = defineProps({ id: { type: String, required: true } })
const { t } = useLocale()
const { isAuthenticated } = useSession()

const thread = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const replyAttachments = ref([])
const reply = reactive({ body: '' })

const canReply = computed(() => reply.body.trim() && !saving.value)

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

function addReplyAttachment(file) {
  replyAttachments.value.push(file)
}

function removeReplyAttachment(fileId) {
  replyAttachments.value = replyAttachments.value.filter((file) => file.id !== fileId)
}

async function loadThread() {
  loading.value = true
  error.value = ''
  try {
    thread.value = await getThread(props.id)
  } catch (err) {
    error.value = err.message || t('forum.detail.loadError')
  } finally {
    loading.value = false
  }
}

async function submitReply() {
  if (!canReply.value) return
  saving.value = true
  error.value = ''
  try {
    await createPost(thread.value.id, {
      body: reply.body,
      file_ids: replyAttachments.value.map((file) => file.id),
    })
    reply.body = ''
    replyAttachments.value = []
    await loadThread()
  } catch (err) {
    error.value = err.message || t('forum.detail.replyError')
  } finally {
    saving.value = false
  }
}

onMounted(loadThread)
</script>

<template>
  <section class="forum-detail-page" aria-labelledby="forum-detail-title">
    <div class="wire-frame page-frame detail-frame forum-detail-frame">
      <header class="wire-section detail-header forum-detail-header">
        <RouterLink class="small-action" to="/forum">{{ t('common.back') }}</RouterLink>
        <div v-if="thread">
          <p class="eyebrow">{{ t(`forum.categories.${thread.category}`) }}</p>
          <h1 id="forum-detail-title">{{ thread.title }}</h1>
          <p>{{ t('forum.detail.meta', { name: thread.owner.display_name, value: formatDate(thread.created_at) }) }}</p>
        </div>
      </header>

      <p v-if="loading" class="wire-section muted">{{ t('forum.detail.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text">{{ error }}</p>

      <template v-else-if="thread">
        <article v-for="post in thread.posts" :key="post.id" class="wire-section content-post-card">
          <div class="post-heading">
            <strong>{{ post.author.display_name }}</strong>
            <span>{{ formatDate(post.created_at) }}</span>
          </div>
          <p class="preserve-lines">{{ post.body }}</p>
          <AttachmentGallery :attachments="post.attachments" />
        </article>

        <section v-if="isAuthenticated" class="wire-section form-section reply-panel">
          <div class="section-title"><span>↳</span><h2>{{ t('forum.detail.replyTitle') }}</h2></div>
          <label class="input-panel embedded-field textarea-shell">
            <textarea v-model="reply.body" rows="5" maxlength="8000" :placeholder="t('forum.detail.replyPlaceholder')"></textarea>
          </label>
          <FileUploadPanel usage-context="forum" @uploaded="addReplyAttachment" />
          <AttachmentGallery :attachments="replyAttachments" />
          <div v-if="replyAttachments.length" class="attachment-chip-row">
            <button v-for="file in replyAttachments" :key="file.id" class="chip-remove" type="button" @click="removeReplyAttachment(file.id)">× {{ file.original_name }}</button>
          </div>
          <button class="wire-section form-button primary" type="button" :disabled="!canReply" @click="submitReply">
            {{ saving ? t('forum.detail.replySaving') : t('forum.detail.reply') }}
          </button>
        </section>

        <RouterLink v-else class="wire-section form-button primary login-callout" to="/login">{{ t('forum.detail.loginToReply') }}</RouterLink>
      </template>
    </div>
  </section>
</template>
