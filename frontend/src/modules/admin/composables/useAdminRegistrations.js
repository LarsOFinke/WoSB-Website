import { computed, reactive, ref, watch } from 'vue'

import {
  approveRegistrationRequest,
  listRegistrationRequests,
  rejectRegistrationRequest,
} from '@/modules/admin/api/admin'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

export function useAdminRegistrations({ isStaff, t, loadUsers }) {
  const registrationRequests = ref([])
  const registrationStatus = ref('pending')
  const registrationSearch = ref('')
  const registrationFromDate = ref('')
  const registrationToDate = ref('')
  const registrationLoading = ref(false)
  const registrationError = ref('')
  const registrationDecisionNotes = reactive({})

  const pendingRegistrationRows = computed(() => registrationRequests.value.filter((row) => row.status === 'pending'))
  const oldestPendingRequest = computed(() => [...pendingRegistrationRows.value]
    .sort((left, right) => new Date(left.created_at) - new Date(right.created_at))[0] || null)
  const registrationCountLabel = computed(() => registrationRequests.value.length === 1
    ? t('admin.registrations.summaryOne')
    : t('admin.registrations.summaryMany', { count: registrationRequests.value.length }))

  async function loadRegistrations() {
    if (!isStaff.value) return
    registrationLoading.value = true
    registrationError.value = ''
    try {
      registrationRequests.value = await listRegistrationRequests({
        status: registrationStatus.value,
        search: registrationSearch.value,
        fromDate: registrationFromDate.value,
        toDate: registrationToDate.value,
      })
    } catch (err) {
      registrationError.value = err.message || t('admin.registrations.loadError')
    } finally {
      registrationLoading.value = false
    }
  }

  async function approveRegistration(id) {
    registrationError.value = ''
    try {
      await approveRegistrationRequest(id, registrationDecisionNotes[id] || '')
      delete registrationDecisionNotes[id]
      await Promise.all([loadRegistrations(), loadUsers()])
    } catch (err) {
      registrationError.value = err.message || t('admin.registrations.approveError')
    }
  }

  async function rejectRegistration(id) {
    registrationError.value = ''
    try {
      await rejectRegistrationRequest(id, registrationDecisionNotes[id] || '')
      delete registrationDecisionNotes[id]
      await loadRegistrations()
    } catch (err) {
      registrationError.value = err.message || t('admin.registrations.rejectError')
    }
  }

  function resetRegistrationFilters() {
    registrationStatus.value = 'pending'
    registrationSearch.value = ''
    registrationFromDate.value = ''
    registrationToDate.value = ''
  }

  useDebouncedWatch(registrationSearch, loadRegistrations, 240)
  watch([registrationStatus, registrationFromDate, registrationToDate], loadRegistrations)

  return {
    registrationRequests, registrationStatus, registrationSearch, registrationFromDate,
    registrationToDate, registrationLoading, registrationError, registrationDecisionNotes,
    pendingRegistrationRows, oldestPendingRequest, registrationCountLabel,
    loadRegistrations, approveRegistration, rejectRegistration, resetRegistrationFilters,
  }
}
