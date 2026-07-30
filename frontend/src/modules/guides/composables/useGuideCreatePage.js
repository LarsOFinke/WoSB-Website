import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'
import { createGuide, getGuide, updateGuide } from '@/modules/guides/api/guides'
import { localizedGuideCategoryItems } from '@/modules/guides/domain/guideDiscovery'
import {
  createBuildEmbedToken,
  createEmbedToken,
  removeBuildEmbedTokens,
  removeFileEmbedTokens,
  unembeddedAttachments,
  unembeddedBuilds,
} from '@/shared/content/richTextEmbeds'

export function useGuideCreatePage() {
  const route = useRoute()
  const router = useRouter()
  const { t } = useLocale()
  const saving = ref(false)
  const loading = ref(false)
  const loadingBuilds = ref(false)
  const error = ref('')
  const attachments = ref([])
  const availableBuilds = ref([])
  const linkedBuilds = ref([])
  const bodyEditor = ref(null)
  const form = reactive({ title: '', category: 'general', summary: '', body: '' })

  const categories = computed(() => localizedGuideCategoryItems(t))
  const guideId = computed(() => route.params.id ? Number(route.params.id) : null)
  const isEditing = computed(() => Number.isInteger(guideId.value) && guideId.value > 0)
  const canSubmit = computed(() => form.title.trim() && form.body.trim() && !saving.value && !loading.value)
  const galleryAttachments = computed(() => unembeddedAttachments(attachments.value, form.body))
  const linkedBuildCards = computed(() => unembeddedBuilds(linkedBuilds.value, form.body))
  const hasPreview = computed(() => form.body.trim() || attachments.value.length || linkedBuilds.value.length)
  const backTarget = computed(() => isEditing.value ? `/guides/${guideId.value}` : '/guides')

  function addAttachment(file) {
    if (!attachments.value.some((item) => item.id === file.id)) attachments.value.push(file)
  }

  function removeAttachment(fileId) {
    attachments.value = attachments.value.filter((file) => file.id !== fileId)
    form.body = removeFileEmbedTokens(form.body, fileId)
  }

  function addBuildReference(build) {
    if (!build || linkedBuilds.value.some((item) => Number(item.id) === Number(build.id))) return
    linkedBuilds.value.push(build)
  }

  function removeBuildReference(buildId) {
    linkedBuilds.value = linkedBuilds.value.filter((build) => Number(build.id) !== Number(buildId))
    form.body = removeBuildEmbedTokens(form.body, buildId)
  }

  async function insertTextToken(token) {
    if (bodyEditor.value?.insertToken) {
      await bodyEditor.value.insertToken(token)
      return
    }
    form.body = `${form.body}${form.body.endsWith('\n') || !form.body ? '' : '\n\n'}${token}\n\n`
  }

  async function insertAttachment({ file, size }) {
    await insertTextToken(createEmbedToken(file.id, size))
  }

  async function insertBuild({ build, layout }) {
    addBuildReference(build)
    await insertTextToken(createBuildEmbedToken(build.id, layout))
  }

  async function loadBuildCatalog() {
    loadingBuilds.value = true
    try {
      const page = await listBuilds('', '', '', 100, 0)
      availableBuilds.value = page.items || []
    } catch (err) {
      error.value = err.message || t('buildEmbeds.loadError')
    } finally {
      loadingBuilds.value = false
    }
  }

  async function loadGuideForEditing() {
    if (!isEditing.value) return
    loading.value = true
    error.value = ''
    try {
      const guide = await getGuide(guideId.value)
      form.title = guide.title
      form.category = guide.category
      form.summary = guide.summary || ''
      form.body = guide.body
      attachments.value = [...(guide.attachments || [])]
      linkedBuilds.value = [...(guide.builds || [])]
    } catch (err) {
      error.value = err.message || t('guides.edit.loadError')
    } finally {
      loading.value = false
    }
  }

  async function submitGuide() {
    if (!canSubmit.value) return
    saving.value = true
    error.value = ''
    const payload = {
      title: form.title,
      category: form.category,
      summary: form.summary || null,
      body: form.body,
      file_ids: attachments.value.map((file) => file.id),
      build_ids: linkedBuilds.value.map((build) => build.id),
    }
    try {
      const saved = isEditing.value
        ? await updateGuide(guideId.value, payload)
        : await createGuide(payload)
      await router.push(`/guides/${saved.id}`)
    } catch (err) {
      error.value = err.message || t(isEditing.value ? 'guides.edit.saveError' : 'guides.create.saveError')
    } finally {
      saving.value = false
    }
  }

  onMounted(async () => {
    await Promise.all([loadBuildCatalog(), loadGuideForEditing()])
  })

  return {
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
  }
}
