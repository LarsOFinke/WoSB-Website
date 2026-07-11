<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useLocale } from '@/locales'
import { createPost, getThread, updatePost } from '@/modules/forum/api/forum'
import { createEmbedToken, removeFileEmbedTokens, unembeddedAttachments } from '@/shared/content/richTextEmbeds'
import { useSession } from '@/modules/accounts/session'

const props = defineProps({ id: { type: String, required: true } })
const { t } = useLocale()
const { isAuthenticated, isStaff, user } = useSession()

const thread = ref(null)
const loading = ref(false)
const saving = ref(false)
const updating = ref(false)
const error = ref('')
const replyAttachments = ref([])
const replyEditor = ref(null)
const reply = reactive({ body: '' })
const editingPostId = ref(null)
const editAttachments = ref([])
const editEditor = ref(null)
const editForm = reactive({ body: '' })

const canReply = computed(() => reply.body.trim() && !saving.value)
const replyGalleryAttachments = computed(() => unembeddedAttachments(replyAttachments.value, reply.body))
const editGalleryAttachments = computed(() => unembeddedAttachments(editAttachments.value, editForm.body))
const canSaveEdit = computed(() => editForm.body.trim() && !updating.value)
const canManageThread = computed(() => thread.value && user.value && (thread.value.owner_id === user.value.id || isStaff.value))

function postGalleryAttachments(post) {
  return unembeddedAttachments(post.attachments || [], post.body)
}

function canEditPost(post, index) {
  if (index === 0 || !user.value) return false
  return post.author_id === user.value.id || isStaff.value
}

function normalizeForumCategory(value) {
  const normalized = String(value || 'general').trim().toLowerCase()
  if (normalized === 'loistics' || normalized === 'logistic') return 'logistics'
  return normalized || 'general'
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

function wasEdited(post) {
  if (!post?.created_at || !post?.updated_at) return false
  return new Date(post.updated_at).getTime() > new Date(post.created_at).getTime() + 1000
}

function addReplyAttachment(file) {
  if (!replyAttachments.value.some((item) => item.id === file.id)) {
    replyAttachments.value.push(file)
  }
}

function removeReplyAttachment(fileId) {
  replyAttachments.value = replyAttachments.value.filter((file) => file.id !== fileId)
  reply.body = removeFileEmbedTokens(reply.body, fileId)
}

async function insertReplyAttachment({ file, size }) {
  const token = createEmbedToken(file.id, size)
  if (replyEditor.value?.insertToken) {
    await replyEditor.value.insertToken(token)
    return
  }
  reply.body = `${reply.body}${reply.body.endsWith('\n') || !reply.body ? '' : '\n\n'}${token}\n\n`
}

function setEditEditor(component) {
  editEditor.value = component
}

function startPostEdit(post) {
  editingPostId.value = post.id
  editForm.body = post.body
  editAttachments.value = [...(post.attachments || [])]
  error.value = ''
}

function cancelPostEdit() {
  editingPostId.value = null
  editForm.body = ''
  editAttachments.value = []
}

function addEditAttachment(file) {
  if (!editAttachments.value.some((item) => item.id === file.id)) {
    editAttachments.value.push(file)
  }
}

function removeEditAttachment(fileId) {
  editAttachments.value = editAttachments.value.filter((file) => file.id !== fileId)
  editForm.body = removeFileEmbedTokens(editForm.body, fileId)
}

async function insertEditAttachment({ file, size }) {
  const token = createEmbedToken(file.id, size)
  if (editEditor.value?.insertToken) {
    await editEditor.value.insertToken(token)
    return
  }
  editForm.body = `${editForm.body}${editForm.body.endsWith('\n') || !editForm.body ? '' : '\n\n'}${token}\n\n`
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

async function submitPostEdit() {
  if (!editingPostId.value || !canSaveEdit.value) return
  updating.value = true
  error.value = ''
  try {
    await updatePost(editingPostId.value, {
      body: editForm.body,
      file_ids: editAttachments.value.map((file) => file.id),
    })
    cancelPostEdit()
    await loadThread()
  } catch (err) {
    error.value = err.message || t('forum.detail.editPostError')
  } finally {
    updating.value = false
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
          <p class="eyebrow">{{ t(`forum.categories.${normalizeForumCategory(thread.category)}`) }}</p>
          <h1 id="forum-detail-title">{{ thread.title }}</h1>
          <p>{{ t('forum.detail.meta', { name: thread.owner.display_name, value: formatDate(thread.created_at) }) }}</p>
          <RouterLink v-if="canManageThread" class="small-action" :to="`/forum/${thread.id}/edit`">
            {{ t('forum.detail.editThread') }}
          </RouterLink>
        </div>
      </header>

      <p v-if="loading" class="wire-section muted">{{ t('forum.detail.loading') }}</p>
      <p v-else-if="error && !thread" class="wire-section error-text">{{ error }}</p>

      <template v-else-if="thread">
        <p v-if="error" class="wire-section error-text">{{ error }}</p>
        <article v-for="(post, index) in thread.posts" :key="post.id" class="wire-section content-post-card">
          <div class="post-heading">
            <div>
              <strong>{{ post.author.display_name }}</strong>
              <small v-if="index === 0">{{ t('forum.detail.openingPost') }}</small>
            </div>
            <div class="post-heading-meta">
              <span>{{ formatDate(post.created_at) }}</span>
              <small v-if="wasEdited(post)">{{ t('forum.detail.edited', { value: formatDate(post.updated_at) }) }}</small>
            </div>
          </div>

          <template v-if="editingPostId === post.id">
            <div class="inline-post-editor">
              <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
              <MarkdownEditor
                :ref="setEditEditor"
                v-model="editForm.body"
                :rows="8"
                :maxlength="8000"
                :placeholder="t('forum.detail.replyPlaceholder')"
                required
              />
              <FileUploadPanel usage-context="forum" @uploaded="addEditAttachment" />
              <AttachmentInsertPanel
                :attachments="editAttachments"
                @insert="insertEditAttachment"
                @remove="removeEditAttachment"
              />
              <AttachmentGallery :attachments="editGalleryAttachments" />
              <section v-if="editForm.body.trim() || editAttachments.length" class="reply-preview-panel">
                <p class="eyebrow">{{ t('files.previewTitle') }}</p>
                <RichTextRenderer :body="editForm.body" :attachments="editAttachments" />
                <AttachmentGallery :attachments="editGalleryAttachments" />
              </section>
              <div class="content-management-actions">
                <button class="form-button primary" type="button" :disabled="!canSaveEdit" @click="submitPostEdit">
                  {{ updating ? t('forum.detail.savingPost') : t('forum.detail.savePost') }}
                </button>
                <button class="small-action" type="button" :disabled="updating" @click="cancelPostEdit">
                  {{ t('common.cancel') }}
                </button>
              </div>
            </div>
          </template>

          <template v-else>
            <RichTextRenderer :body="post.body" :attachments="post.attachments" />
            <AttachmentGallery :attachments="postGalleryAttachments(post)" />
            <div v-if="canEditPost(post, index)" class="post-actions">
              <button class="small-action" type="button" @click="startPostEdit(post)">
                {{ t('forum.detail.editPost') }}
              </button>
            </div>
          </template>
        </article>

        <section v-if="isAuthenticated" class="wire-section form-section reply-panel">
          <div class="section-title"><span>↳</span><h2>{{ t('forum.detail.replyTitle') }}</h2></div>
          <p class="section-helper-text">{{ t('markdown.editorHint') }}</p>
          <MarkdownEditor
            ref="replyEditor"
            v-model="reply.body"
            :rows="5"
            :maxlength="8000"
            :placeholder="t('forum.detail.replyPlaceholder')"
            required
          />
          <FileUploadPanel usage-context="forum" @uploaded="addReplyAttachment" />
          <AttachmentInsertPanel :attachments="replyAttachments" @insert="insertReplyAttachment" @remove="removeReplyAttachment" />
          <AttachmentGallery :attachments="replyGalleryAttachments" />
          <section v-if="reply.body.trim() || replyAttachments.length" class="reply-preview-panel">
            <p class="eyebrow">{{ t('files.previewTitle') }}</p>
            <RichTextRenderer :body="reply.body" :attachments="replyAttachments" />
            <AttachmentGallery :attachments="replyGalleryAttachments" />
          </section>
          <button class="wire-section form-button primary" type="button" :disabled="!canReply" @click="submitReply">
            {{ saving ? t('forum.detail.replySaving') : t('forum.detail.reply') }}
          </button>
        </section>

        <RouterLink v-else class="wire-section form-button primary login-callout" to="/login">{{ t('forum.detail.loginToReply') }}</RouterLink>
      </template>
    </div>
  </section>
</template>
