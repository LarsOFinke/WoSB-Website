import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getBackupControlStatus, runApplicationBackup } from '@/modules/admin/api/admin'
import { formatBackupBytes, formatBackupDateTime } from '@/modules/admin/domain/backupPresentation'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const EMPTY_STATUS = {
  state: 'idle',
  operation: 'idle',
  message: '',
  connection: { configured: false, write_tested_at: null },
  artifacts: [],
  request_available: false,
}

export function useDatabaseBackupsPage() {
  const { locale, t } = useLocale()
  const { isAdmin, user } = useSession()
  const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
  const status = ref({ ...EMPTY_STATUS })
  const loading = ref(false)
  const error = ref('')
  const success = ref('')
  const hostApproval = ref('')
  let pollTimer = null

  const inProgress = computed(() => ['queued', 'running'].includes(status.value.state))
  const configured = computed(() => Boolean(status.value.connection?.configured))
  const connectionReady = computed(() => (
    configured.value && Boolean(status.value.connection?.write_tested_at)
  ))
  const canSubmit = computed(() => (
    !loading.value && !inProgress.value && status.value.request_available !== false
  ))
  const stateLabel = computed(() => t(`admin.backups.states.${status.value.state || 'idle'}`))
  const operationLabel = computed(() => t(`admin.backups.operations.${status.value.operation || 'idle'}`))

  const formatDateTime = (value) => formatBackupDateTime(value, locale.value)
  const formatBytes = formatBackupBytes

  function schedulePoll() {
    window.clearTimeout(pollTimer)
    if (!inProgress.value) return
    pollTimer = window.setTimeout(async () => {
      await loadStatus({ quiet: true })
      schedulePoll()
    }, 2500)
  }

  async function loadStatus({ quiet = false } = {}) {
    if (!quiet) loading.value = true
    if (!quiet) error.value = ''
    try {
      const previousState = status.value.state
      status.value = await getBackupControlStatus()
      if (previousState && ['queued', 'running'].includes(previousState)
        && status.value.state === 'succeeded') {
        success.value = status.value.message
      }
      if (status.value.state === 'failed') error.value = status.value.message
    } catch (err) {
      if (!quiet) error.value = err.message || t('admin.backups.errors.load')
    } finally {
      if (!quiet) loading.value = false
    }
  }

  async function runBackup() {
    if (!window.confirm(t('admin.backups.confirmRun'))) return
    loading.value = true
    error.value = ''
    success.value = ''
    try {
      const response = await runApplicationBackup(hostApproval.value)
      hostApproval.value = ''
      status.value = response.status
      success.value = t('admin.backups.messages.backupQueued')
      schedulePoll()
    } catch (err) {
      error.value = err.message || t('admin.backups.errors.request')
    } finally {
      loading.value = false
    }
  }

  onMounted(async () => {
    await loadStatus()
    schedulePoll()
  })
  onUnmounted(() => window.clearTimeout(pollTimer))

  return {
    t, isAdmin, user, navigationGroups, status, loading, error, success, hostApproval,
    inProgress, configured, connectionReady, canSubmit, stateLabel, operationLabel,
    formatDateTime, formatBytes, loadStatus, runBackup,
  }
}
