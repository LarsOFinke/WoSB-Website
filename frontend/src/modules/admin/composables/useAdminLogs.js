import { computed, ref, watch } from 'vue'

import { getAdminLogSummary, listAdminLogs } from '@/modules/admin/api/admin'
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
  const logSort = ref('created_at')
  const logOrder = ref('desc')
  const logsLoading = ref(false)
  const logsError = ref('')

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
    }
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

  function openLogsForIp(ipAddress) {
    if (!isAdmin.value) return
    logIp.value = ipAddress || ''
    activeTab.value = 'logs'
  }

  watch([logLevel, logIp, logThreat, logFromDate, logToDate, logSort, logOrder], loadLogs)
  useDebouncedWatch(logPath, loadLogs, 260)

  return {
    appLogs, logSummary, logLevel, logPath, logIp, logThreat, logFromDate, logToDate,
    logSort, logOrder, logsLoading, logsError, logsCountLabel,
    loadLogs, formatDuration, openLogsForIp,
  }
}
