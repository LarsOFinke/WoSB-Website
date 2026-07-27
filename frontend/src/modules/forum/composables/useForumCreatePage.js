import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { createThread, getThread, updateThread } from '@/modules/forum/api/forum'
import { createEmbedToken, removeFileEmbedTokens, unembeddedAttachments } from '@/shared/content/richTextEmbeds'

export function useForumCreatePage() {
  const route = useRoute()
  const router = useRouter()
  const { t } = useLocale()
  const saving = ref(false)
  const loading = ref(false)
  const error = ref('')
  const attachments = ref([])
  const bodyEditor = ref(null)

  const categories = ['general', 'builds', 'events', 'support', 'training', 'logistics']
  const form = reactive({ title: '', category: 'general', body: '' })
  const threadId = computed(() => route.params.id ? Number(route.params.id) : null)
  const isEditing = computed(() => Number.isInteger(threadId.value) && threadId.value > 0)
  const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value && !loading.value)
  const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
  const hasPreview = computed(() => form.body.trim() || attachments.value.length)
  const backTarget = computed(() => isEditing.value ? `/forum/${threadId.value}` : '/forum')

  function addAttachment(file) {
    if (!attachments.value.some((item) => item.id === file.id)) {
      attachments.value.push(file)
    }
  }

  function removeAttachment(fileId) {
    attachments.value = attachments.value.filter((file) => file.id !== fileId)
    form.body = removeFileEmbedTokens(form.body, fileId)
  }

  async function insertAttachment({ file, size }) {
    const token = createEmbedToken(file.id, size)
    if (bodyEditor.value?.insertToken) {
      await bodyEditor.value.insertToken(token)
      return
    }
    form.body = `${form.body}${form.body.endsWith('\n') || !form.body ? '' : '\n\n'}${token}\n\n`
  }

  async function loadThreadForEditing() {
    if (!isEditing.value) return
    loading.value = true
    error.value = ''
    try {
      const thread = await getThread(threadId.value)
      const openingPost = thread.posts?.[0]
      form.title = thread.title
      form.category = thread.category
      form.body = openingPost?.body || ''
      attachments.value = [...(openingPost?.attachments || [])]
    } catch (err) {
      error.value = err.message || t('forum.edit.loadError')
    } finally {
      loading.value = false
    }
  }

  async function submitThread() {
    if (!canSubmit.value) return
    saving.value = true
    error.value = ''
    const payload = {
      title: form.title,
      category: form.category,
      body: form.body,
      file_ids: attachments.value.map((file) => file.id),
    }
    try {
      const saved = isEditing.value
        ? await updateThread(threadId.value, payload)
        : await createThread(payload)
      await router.push(`/forum/${saved.id}`)
    } catch (err) {
      error.value = err.message || t(isEditing.value ? 'forum.edit.saveError' : 'forum.create.saveError')
    } finally {
      saving.value = false
    }
  }

  onMounted(loadThreadForEditing)

  return {
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
  }
}
