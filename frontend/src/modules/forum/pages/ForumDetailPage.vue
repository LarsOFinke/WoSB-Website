<script setup>
import AttachmentGallery from '@/core/components/AttachmentGallery.vue'
import AttachmentInsertPanel from '@/core/components/AttachmentInsertPanel.vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MarkdownEditor from '@/core/components/MarkdownEditor.vue'
import RichTextRenderer from '@/core/components/RichTextRenderer.vue'
import { useForumDetailPage } from '@/modules/forum/composables/useForumDetailPage'
import '@/modules/forum/styles/forumReplies.css'

const props = defineProps({ id: { type: String, required: true } })
const {
  t,
  isStaff,
  thread,
  loading,
  saving,
  updating,
  deletingPostId,
  pendingDeletePostId,
  error,
  replyAttachments,
  replyEditor,
  reply,
  editingPostId,
  editAttachments,
  editEditor,
  editForm,
  canReply,
  replyGalleryAttachments,
  editGalleryAttachments,
  canSaveEdit,
  canManageThread,
  postGalleryAttachments,
  canEditPost,
  canDeletePost,
  askDeletePost,
  cancelDeletePost,
  normalizeForumCategory,
  formatDate,
  wasEdited,
  addReplyAttachment,
  removeReplyAttachment,
  insertReplyAttachment,
  setEditEditor,
  startPostEdit,
  cancelPostEdit,
  addEditAttachment,
  removeEditAttachment,
  insertEditAttachment,
  loadThread,
  submitReply,
  submitPostEdit,
  submitPostDelete,
  createEmbedToken,
  removeFileEmbedTokens,
  unembeddedAttachments,
} = useForumDetailPage(props)
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
            <div v-if="canEditPost(post, index) || canDeletePost(post, index)" class="post-actions forum-post-management-actions">
              <template v-if="pendingDeletePostId === post.id">
                <div class="forum-post-delete-confirmation" role="alert">
                  <div><strong>{{ t('forum.detail.deletePostConfirmTitle') }}</strong><span>{{ t('forum.detail.deletePostConfirmText') }}</span></div>
                  <div class="compact-actions">
                    <button class="danger-action" type="button" :disabled="deletingPostId === post.id" @click="submitPostDelete(post)">{{ deletingPostId === post.id ? t('forum.detail.deletingPost') : t('forum.detail.deletePostNow') }}</button>
                    <button class="small-action" type="button" :disabled="deletingPostId === post.id" @click="cancelDeletePost">{{ t('common.cancel') }}</button>
                  </div>
                </div>
              </template>
              <template v-else>
                <button v-if="canEditPost(post, index)" class="small-action" type="button" @click="startPostEdit(post)">{{ t('forum.detail.editPost') }}</button>
                <button v-if="canDeletePost(post, index)" class="danger-action" type="button" @click="askDeletePost(post.id)">{{ t('forum.detail.deletePost') }}</button>
              </template>
            </div>
          </template>
        </article>

        <section v-if="isStaff" class="wire-section form-section reply-panel">
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
