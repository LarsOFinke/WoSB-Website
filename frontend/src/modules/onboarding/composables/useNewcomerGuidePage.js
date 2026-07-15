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
  resetGuideResource,
  resourceComponent,
  resourceTarget,
} from '@/modules/onboarding/domain/newcomerGuideDraft'
import { appendLinkedResource } from '@/modules/onboarding/services/newcomerGuideResources'

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

  const resourceTypeOptions = computed(() => [
    { value: 'guide', label: t('newcomerGuide.editor.types.guide') },
    { value: 'build', label: t('newcomerGuide.editor.types.build') },
    { value: 'internal', label: t('newcomerGuide.editor.types.internal') },
    { value: 'external', label: t('newcomerGuide.editor.types.external') },
  ])

  const emptyTextBlock = () => createGuideBlock('text')
  const emptyResourceBlock = () => createGuideBlock('resources')
  const emptyResource = () => createGuideResource()
  const toDraft = (source) => createGuideDraft(source)
  const normalizePayload = () => guidePayload(draft.value)

  async function loadResourceOptions() {
    if (resourceOptionsLoaded.value || resourceOptionsLoading.value) return
    resourceOptionsLoading.value = true
    resourceOptionsError.value = ''
    try {
      const [guideRows, buildRows] = await Promise.all([listGuides(), listBuilds()])
      guides.value = guideRows
      builds.value = buildRows
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
    await loadResourceOptions()
  }

  function cancelEditing() {
    editing.value = false
    draft.value = null
    error.value = ''
  }

  function addBlock(type) {
    draft.value.blocks.push(createGuideBlock(type === 'resources' ? 'resources' : 'text'))
  }

  function removeBlock(index) {
    draft.value.blocks.splice(index, 1)
  }

  function moveBlock(index, delta) {
    moveArrayItem(draft.value.blocks, index, delta)
  }

  function addResource(block) {
    block.resources.push(createGuideResource())
  }

  function addLinkedResource(resourceType) {
    const block = appendLinkedResource(draft.value.blocks, resourceType)
    if (!block) return
    if (!block.title) block.title = t('newcomerGuide.resourceSection')
    block.resources.at(-1).resource_id = null
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

  return {
    t, isStaff, page, draft, guides, builds, loading, saving, editing, error,
    success, resourceOptionsLoading, resourceOptionsLoaded, resourceOptionsError,
    resourceTypeOptions, emptyTextBlock, emptyResourceBlock, emptyResource,
    toDraft, normalizePayload, resourceComponent, resourceTarget, loadResourceOptions,
    startEditing, cancelEditing, addBlock, removeBlock, moveBlock, addResource,
    addLinkedResource, removeResource, moveResource, onResourceTypeChange,
    loadPage, savePage,
  }
}
