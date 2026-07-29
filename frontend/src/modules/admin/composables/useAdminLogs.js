import { computed, ref } from 'vue'

import { getSecurityDashboard } from '@/modules/admin/api/admin'
import { isoDate, shiftDate } from '@/modules/admin/domain/adminWorkspace'

const EMPTY_SECURITY_SUMMARY = {
  total_events: 0,
  unique_ips: 0,
  threat_score: 0,
  threat_level: 'low',
  threat_counts: { low: 0, guarded: 0, elevated: 0, critical: 0 },
  signal_counts: { reconnaissance: 0, login_failure: 0, rate_limit: 0 },
}

export function useAdminLogs({ isAdmin, activeTab, t }) {
  const today = new Date()
  const logSummary = ref({ ...EMPTY_SECURITY_SUMMARY })
  const logIp = ref('')
  const logThreat = ref('')
  const logFromDate = ref(isoDate(shiftDate(today, -6)))
  const logToDate = ref(isoDate(today))
  const logsLoading = ref(false)
  const logsError = ref('')

  const logsCountLabel = computed(() => t('admin.logs.summary', {
    count: logSummary.value.total_events || 0,
  }))

  async function loadLogs() {
    if (!isAdmin.value) return null
    logsLoading.value = true
    logsError.value = ''
    try {
      const result = await getSecurityDashboard({
        fromDate: logFromDate.value,
        toDate: logToDate.value,
        threatLevel: logThreat.value,
        clientIp: logIp.value,
        limit: 250,
      })
      logSummary.value = result
      return result
    } catch (err) {
      logsError.value = err.message || t('admin.security.loadError')
      return null
    } finally {
      logsLoading.value = false
    }
  }

  function applyDashboardSummary(result) {
    if (result) logSummary.value = result
  }


  return {
    logSummary, logIp, logThreat, logFromDate, logToDate,
    logsLoading, logsError, logsCountLabel,
    loadLogs, applyDashboardSummary,
  }
}
