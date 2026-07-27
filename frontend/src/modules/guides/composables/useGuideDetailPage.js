import { computed, onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { deleteGuide, getGuide } from '@/modules/guides/api/guides'
import { useGuidePrintActions } from '@/modules/guides/composables/useGuidePrintActions'
import { formatGuideDate, guideHeadingNavigation } from '@/modules/guides/domain/guidePresentation'
import { unembeddedAttachments, unembeddedBuilds } from '@/shared/content/richTextEmbeds'

export function useGuideDetailPage(props) {
  const { t } = useLocale()
  const { isStaff, user } = useSession()
  const guide = ref(null)
  const loading = ref(false)
  const deleting = ref(false)
  const error = ref('')
  const { printBusy, printStatus, printGuide } = useGuidePrintActions(guide, { t })

  const canManage = computed(() => guide.value && user.value
    && (guide.value.owner_id === user.value.id || isStaff.value))
  const galleryAttachments = computed(() => guide.value
    ? unembeddedAttachments(guide.value.attachments || [], guide.value.body)
    : [])
  const linkedBuildCards = computed(() => guide.value
    ? unembeddedBuilds(guide.value.builds || [], guide.value.body)
    : [])
  const headings = computed(() => guideHeadingNavigation(guide.value?.body))

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

  return {
    t,
    isStaff,
    user,
    guide,
    loading,
    deleting,
    error,
    printBusy,
    printStatus,
    printGuide,
    canManage,
    galleryAttachments,
    linkedBuildCards,
    headings,
    loadGuide,
    submitDelete,
    useGuidePrintActions,
    formatGuideDate,
    guideHeadingNavigation,
    unembeddedAttachments,
    unembeddedBuilds,
  }
}
