import { computed, onMounted, reactive, ref } from 'vue'
import { useLocale } from '@/locales'
import { createPost, deletePost, getThread, updatePost } from '@/modules/forum/api/forum'
import { createEmbedToken, removeFileEmbedTokens, unembeddedAttachments } from '@/shared/content/richTextEmbeds'
import { useSession } from '@/modules/accounts/session'

export function useForumDetailPage(props) {
  const { t } = useLocale()
  const { isAuthenticated, isStaff, user } = useSession()

  const thread = ref(null)
  const loading = ref(false)
  const saving = ref(false)
  const updating = ref(false)
  const deletingPostId = ref(null)
  const pendingDeletePostId = ref(null)
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

  function canDeletePost(post, index) {
    return canEditPost(post, index)
  }

  function askDeletePost(postId) {
    pendingDeletePostId.value = postId
    error.value = ''
  }

  function cancelDeletePost() {
    pendingDeletePostId.value = null
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

  async function submitPostDelete(post) {
    if (!post || pendingDeletePostId.value !== post.id) return
    deletingPostId.value = post.id
    error.value = ''
    try {
      await deletePost(post.id)
      pendingDeletePostId.value = null
      if (editingPostId.value === post.id) cancelPostEdit()
      await loadThread()
    } catch (err) {
      error.value = err.message || t('forum.detail.deletePostError')
    } finally {
      deletingPostId.value = null
    }
  }

  onMounted(loadThread)

  return {
    t,
    isAuthenticated,
    isStaff,
    user,
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
  }
}
