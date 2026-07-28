import { computed, ref, watch } from 'vue'

import {
  deleteAdminLog,
  deleteFilteredAdminLogs,
  getAdminLogSummary,
  listAdminLogs,
} from '@/modules/admin/api/admin'
import { formatDuration, isoDate, shiftDate } from '@/modules/admin/domain/adminWorkspace'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

const EMPTY_LOG_SUMMARY = { total: 0, errors: 0, warnings: 0, slow_requests: 0, recent_status: {} }

export function useAdminLogs({ isAdmin, activeTab, t }) {
  const today = new Date()
  const appLogs = ref([])
  const logSummary = ref({ ...EMPTY_LOG_SUMMARY })
  const logLevel = ref('')
  const logPath = ref('')
  const logIp = ref('')
  const logThreat = ref('')
  const logFromDate = ref(isoDate(shiftDate(today, -6)))
  const logToDate = ref(isoDate(today))
  const logIncludeBlocked = ref(false)
  const logSort = ref('created_at')
  const logOrder = ref('desc')
  const logsLoading = ref(false)
  const logsDeleting = ref(false)
  const logsError = ref('')
  const logsActionError = ref('')
  const logsActionSuccess = ref('')

  const logsCountLabel = computed(() => t('admin.logs.summary', {
    count: logSummary.value.total || appLogs.value.length,
  }))

  function query() {
    return {
      level: logLevel.value,
      path: logPath.value,
      clientIp: logIp.value,
      threatLevel: logThreat.value,
      fromDate: logFromDate.value,
      toDate: logToDate.value,
      includeBlocked: logIncludeBlocked.value,
    }
  }

  function clearLogActionState() {
    logsActionError.value = ''
    logsActionSuccess.value = ''
  }

  async function loadLogs() {
    if (!isAdmin.value) return
    logsLoading.value = true
    logsError.value = ''
    try {
      const filters = query()
      const [summary, rows] = await Promise.all([
        getAdminLogSummary(filters),
        listAdminLogs({ ...filters, sort: logSort.value, order: logOrder.value, limit: 140 }),
      ])
      logSummary.value = summary
      appLogs.value = rows
    } catch (err) {
      logsError.value = err.message || t('admin.logs.loadError')
    } finally {
      logsLoading.value = false
    }
  }

  async function deleteLogEntry(id) {
    if (!isAdmin.value || !id) return false
    logsDeleting.value = true
    clearLogActionState()
    try {
      await deleteAdminLog(id)
      logsActionSuccess.value = t('admin.logs.deleteOneSuccess')
      await loadLogs()
      return true
    } catch (err) {
      logsActionError.value = err.message || t('admin.logs.deleteError')
      return false
    } finally {
      logsDeleting.value = false
    }
  }

  async function deleteFilteredLogs() {
    if (!isAdmin.value) return 0
    logsDeleting.value = true
    clearLogActionState()
    try {
      const result = await deleteFilteredAdminLogs(query())
      const deletedCount = Number(result?.deleted_count || 0)
      logsActionSuccess.value = t('admin.logs.deleteFilteredSuccess', { count: deletedCount })
      await loadLogs()
      return deletedCount
    } catch (err) {
      logsActionError.value = err.message || t('admin.logs.deleteError')
      return -1
    } finally {
      logsDeleting.value = false
    }
  }

  function openLogsForIp(ipAddress) {
    if (!isAdmin.value) return
    logIp.value = ipAddress || ''
    logIncludeBlocked.value = Boolean(ipAddress)
    activeTab.value = 'logs'
  }

  watch(
    [logLevel, logIp, logThreat, logFromDate, logToDate, logIncludeBlocked, logSort, logOrder],
    loadLogs,
  )
  useDebouncedWatch(logPath, loadLogs, 260)

  return {
    appLogs, logSummary, logLevel, logPath, logIp, logThreat, logFromDate, logToDate,
    logIncludeBlocked, logSort, logOrder, logsLoading, logsDeleting, logsError,
    logsActionError, logsActionSuccess, logsCountLabel,
    loadLogs, deleteLogEntry, deleteFilteredLogs, clearLogActionState,
    formatDuration, openLogsForIp,
  }
}
