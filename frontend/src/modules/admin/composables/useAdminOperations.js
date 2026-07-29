import { ref } from 'vue'

import { getIpBlockSummary } from '@/modules/admin/api/admin'

export function useAdminOperations({ isAdmin, activeTab, t, logs }) {
  const ipBlockPrefill = ref('')
  const ipBlockOverview = ref({ total: 0, active: 0, permanent: 0, temporary: 0, expired: 0, unblocked: 0 })
  const apiStatus = ref(t('admin.status.loading'))
  const apiStatusDetail = ref(t('admin.status.loadingDetail'))

  async function loadStatus() {
    if (!isAdmin.value) return
    apiStatus.value = t('admin.status.loading')
    apiStatusDetail.value = t('admin.status.loadingDetail')
    try {
      const response = await fetch('/api/health')
      if (!response.ok) throw new Error(`API responded with ${response.status}`)
      const payload = await response.json()
      apiStatus.value = t('admin.status.online')
      apiStatusDetail.value = payload.status
        ? t('admin.status.detailWithStatus', { status: payload.status })
        : t('admin.status.onlineDetail')
    } catch {
      apiStatus.value = t('admin.status.offline')
      apiStatusDetail.value = t('admin.status.offlineDetail')
    }
  }

  async function loadAdminOverviewMetrics() {
    if (!isAdmin.value) return
    try {
      const [securitySummary, blocks] = await Promise.all([
        logs.loadLogs(),
        getIpBlockSummary(),
      ])
      if (securitySummary) logs.logSummary.value = securitySummary
      ipBlockOverview.value = blocks
    } catch (err) {
      logs.logsError.value = err.message || t('admin.workspace.overviewLoadError')
    }
  }

  function openIpBlockManager(ipAddress) {
    if (!isAdmin.value) return
    ipBlockPrefill.value = ipAddress || ''
    activeTab.value = 'ip-blocks'
  }

  return {
    ipBlockPrefill, ipBlockOverview, apiStatus, apiStatusDetail,
    loadStatus, loadAdminOverviewMetrics, openIpBlockManager,
  }
}
