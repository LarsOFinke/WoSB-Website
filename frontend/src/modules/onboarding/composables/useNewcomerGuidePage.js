import { computed, onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { listBuilds } from '@/modules/builds/api/builds'
import { listGuides } from '@/modules/guides/api/guides'
import { getNewcomerGuide, updateNewcomerGuide } from '@/modules/onboarding/api/newcomerGuide'
import {
  createGuideBlock,
  createGuideDraft,
  createGuideResource,
  guidePayload,
  moveArrayItem,
  moveSelectedItem,
  resetGuideResource,
} from '@/modules/onboarding/domain/newcomerGuideDraft'

export function useNewcomerGuidePage() {
  const { t } = useLocale()
  const { isStaff } = useSession()
  const page = ref(null)
  const draft = ref(null)
  const guides = ref([])
  const builds = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const editing = ref(false)
  const error = ref('')
  const success = ref('')
  const resourceOptionsLoading = ref(false)
  const resourceOptionsLoaded = ref(false)
  const resourceOptionsError = ref('')
  const activeFolderIndex = ref(-1)

  const visibleFolders = computed(() => editing.value ? (draft.value?.blocks || []) : (page.value?.blocks || []))
  const activeFolder = computed(() => visibleFolders.value[activeFolderIndex.value] || null)

  const resourceTypeOptions = computed(() => [
    { value: 'guide', label: t('newcomerGuide.editor.types.guide') },
    { value: 'build', label: t('newcomerGuide.editor.types.build') },
    { value: 'internal', label: t('newcomerGuide.editor.types.internal') },
    { value: 'external', label: t('newcomerGuide.editor.types.external') },
  ])

  async function loadResourceOptions() {
    if (resourceOptionsLoaded.value || resourceOptionsLoading.value) return
    resourceOptionsLoading.value = true
    resourceOptionsError.value = ''
    try {
      const [guideRows, buildRows] = await Promise.all([listGuides(), listBuilds('', '', '', 100, 0)])
      guides.value = guideRows
      builds.value = buildRows.items || []
      resourceOptionsLoaded.value = true
    } catch (err) {
      resourceOptionsError.value = err.message || t('newcomerGuide.editor.resourceLoadError')
    } finally {
      resourceOptionsLoading.value = false
    }
  }

  async function startEditing() {
    draft.value = createGuideDraft(page.value)
    editing.value = true
    success.value = ''
    activeFolderIndex.value = activeFolderIndex.value < 0
      ? 0
      : Math.min(activeFolderIndex.value, Math.max(0, draft.value.blocks.length - 1))
    await loadResourceOptions()
  }

  function cancelEditing() {
    editing.value = false
    draft.value = null
    error.value = ''
  }

  function addBlock(type) {
    draft.value.blocks.push(createGuideBlock(type === 'resources' ? 'resources' : 'text'))
    activeFolderIndex.value = draft.value.blocks.length - 1
  }

  function removeBlock(index) {
    draft.value.blocks.splice(index, 1)
    if (activeFolderIndex.value > index) activeFolderIndex.value -= 1
    activeFolderIndex.value = Math.min(activeFolderIndex.value, Math.max(0, draft.value.blocks.length - 1))
  }

  function moveBlock(index, delta) {
    activeFolderIndex.value = moveSelectedItem(draft.value.blocks, activeFolderIndex.value, index, delta)
  }

  function addResource(block) {
    block.resources.push(createGuideResource())
  }

  function removeResource(block, index) {
    block.resources.splice(index, 1)
  }

  function moveResource(block, index, delta) {
    moveArrayItem(block.resources, index, delta)
  }

  function onResourceTypeChange(resource) {
    resetGuideResource(resource)
  }

  async function loadPage() {
    loading.value = true
    error.value = ''
    try {
      page.value = await getNewcomerGuide()
      activeFolderIndex.value = -1
    } catch (err) {
      error.value = err.message || t('newcomerGuide.loadError')
    } finally {
      loading.value = false
    }
  }

  async function savePage() {
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      page.value = await updateNewcomerGuide(guidePayload(draft.value))
      activeFolderIndex.value = Math.min(activeFolderIndex.value, Math.max(0, page.value.blocks.length - 1))
      editing.value = false
      draft.value = null
      success.value = t('newcomerGuide.saved')
    } catch (err) {
      error.value = err.message || t('newcomerGuide.saveError')
    } finally {
      saving.value = false
    }
  }

  onMounted(loadPage)

  function selectFolder(index) {
    if (index >= 0 && index < visibleFolders.value.length) activeFolderIndex.value = index
  }

  function showTopicOverview() {
    if (!editing.value) activeFolderIndex.value = -1
  }

  return {
    t, isStaff, page, draft, guides, builds, loading, saving, editing, error,
    success, resourceOptionsLoading, resourceOptionsError,
    resourceTypeOptions, activeFolderIndex, activeFolder, visibleFolders,
    startEditing, cancelEditing, addBlock, removeBlock, moveBlock, addResource,
    removeResource, moveResource, onResourceTypeChange,
    loadPage, savePage, selectFolder, showTopicOverview,
  }
}
