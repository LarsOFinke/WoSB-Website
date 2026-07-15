import { computed, ref } from 'vue'

import { deleteAdminForumThread, deleteAdminGuide, listAdminForumThreads, listAdminGuides } from '@/modules/admin/api/admin'
import { closeGroup, listGroups } from '@/modules/groups/api/groups'
import { countVisibleContent, ownerMatches } from '@/modules/admin/domain/adminWorkspace'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

export function useAdminContent({ isStaff, t, clearConfirmation }) {
  const forumThreads = ref([])
  const guides = ref([])
  const groups = ref([])
  const contentSearch = ref('')
  const contentScope = ref('all')
  const contentOwner = ref('')
  const contentLoading = ref(false)
  const contentError = ref('')

  const visibleForumThreads = computed(() => forumThreads.value.filter((row) => ownerMatches(row, contentOwner.value)))
  const visibleGuides = computed(() => guides.value.filter((row) => ownerMatches(row, contentOwner.value)))
  const visibleGroups = computed(() => groups.value.filter((row) => ownerMatches(row, contentOwner.value)))
  const visibleContentCount = computed(() => countVisibleContent(contentScope.value, {
    forum: visibleForumThreads.value,
    guides: visibleGuides.value,
    groups: visibleGroups.value,
  }))
  const contentCountLabel = computed(() => t('admin.content.summary', { count: visibleContentCount.value }))

  async function loadContent() {
    if (!isStaff.value) return
    contentLoading.value = true
    contentError.value = ''
    try {
      const [threadRows, guideRows, groupRows] = await Promise.all([
        listAdminForumThreads(contentSearch.value),
        listAdminGuides(contentSearch.value),
        listGroups({ search: contentSearch.value }),
      ])
      forumThreads.value = threadRows
      guides.value = guideRows
      groups.value = groupRows
    } catch (err) {
      contentError.value = err.message || t('admin.content.loadError')
    } finally {
      contentLoading.value = false
    }
  }

  async function runContentAction(action, fallbackMessage) {
    contentError.value = ''
    try {
      await action()
      clearConfirmation()
      await loadContent()
    } catch (err) {
      contentError.value = err.message || t(fallbackMessage)
    }
  }

  function confirmDeleteThread(threadId) {
    return runContentAction(() => deleteAdminForumThread(threadId), 'admin.content.deleteError')
  }

  function confirmDeleteGuide(guideId) {
    return runContentAction(() => deleteAdminGuide(guideId), 'admin.content.deleteError')
  }

  function confirmCloseGroup(groupId) {
    return runContentAction(() => closeGroup(groupId), 'admin.content.closeError')
  }

  function resetContentFilters() {
    contentSearch.value = ''
    contentScope.value = 'all'
    contentOwner.value = ''
  }

  useDebouncedWatch(contentSearch, loadContent, 220)

  return {
    forumThreads, guides, groups, contentSearch, contentScope, contentOwner,
    contentLoading, contentError, visibleForumThreads, visibleGuides, visibleGroups,
    visibleContentCount, contentCountLabel, loadContent, confirmDeleteThread,
    confirmDeleteGuide, confirmCloseGroup, resetContentFilters,
  }
}
