import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getBackupControlStatus, runApplicationBackup } from '@/modules/admin/api/admin'
import { formatBackupBytes, formatBackupDateTime } from '@/modules/admin/domain/backupPresentation'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'
import { useBackupEnrollment } from './useBackupEnrollment'

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
  const clock = ref(Date.now())
  let pollTimer = null
  let clockTimer = null

  const inProgress = computed(() => ['queued', 'running'].includes(status.value.state))
  const configured = computed(() => Boolean(status.value.connection?.configured))
  const connectionReady = computed(() => (
    configured.value && Boolean(status.value.connection?.write_tested_at)
  ))
  const canSubmit = computed(() => (
    !loading.value && !inProgress.value && status.value.request_available !== false
  ))
  const hasHostApproval = computed(() => hostApproval.value.trim().length >= 24)
  const stateLabel = computed(() => t(`admin.backups.states.${status.value.state || 'idle'}`))
  const operationLabel = computed(() => t(`admin.backups.operations.${status.value.operation || 'idle'}`))
  const operationElapsedSeconds = computed(() => {
    const started = Date.parse(status.value.started_at || '')
    if (!Number.isFinite(started)) return 0
    return Math.max(0, Math.floor((clock.value - started) / 1000))
  })
  const operationProgress = computed(() => {
    const message = String(status.value.message || '').toLowerCase()
    if (message.includes('preparing') || message.includes('coordinated')) return 10
    if (message.includes('local backup set')) return 45
    if (message.includes('core artifacts')) return 65
    if (message.includes('recovery material')) return 80
    if (message.includes('remote ingest')) return 90
    return inProgress.value ? null : (status.value.state === 'succeeded' ? 100 : 0)
  })

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

  async function request(action, successKey) {
    if (!canSubmit.value) {
      error.value = status.value.message || t('admin.backups.errors.request')
      return
    }
    if (!hasHostApproval.value) {
      error.value = `${t('admin.backups.restore.approvalToken')}: ${t('admin.backups.restore.approvalPlaceholder')}`
      return
    }
    loading.value = true
    error.value = ''
    success.value = ''
    try {
      const response = await action(hostApproval.value.trim())
      hostApproval.value = ''
      status.value = response.status
      success.value = t(successKey)
      schedulePoll()
    } catch (err) {
      error.value = err.message || t('admin.backups.errors.request')
    } finally {
      loading.value = false
    }
  }

  const {
    response: enrollmentResponse,
    responseFileName: enrollmentFileName,
    setup: enrollmentSetup,
    enrollmentRequest,
    responsePreview: enrollmentResponsePreview,
    setupError: enrollmentSetupError,
    progress: enrollmentProgress,
    responseError: enrollmentResponseError,
    command: enrollmentCommand,
    canCopyCommand: canCopyEnrollmentCommand,
    canApply: canApplyEnrollment,
    copyCommand: copyEnrollmentCommand,
    prepare: prepareEnrollment,
    downloadRequest: downloadEnrollmentRequest,
    loadResponse: loadEnrollmentResponse,
    apply: applyEnrollment,
  } = useBackupEnrollment({ status, canSubmit, error, success, request, t })

  onMounted(async () => {
    clockTimer = window.setInterval(() => { clock.value = Date.now() }, 1000)
    await loadStatus()
    schedulePoll()
  })
  onUnmounted(() => {
    window.clearTimeout(pollTimer)
    window.clearInterval(clockTimer)
  })

  return {
    t, isAdmin, user, navigationGroups, status, loading, error, success, hostApproval,
    inProgress, configured, connectionReady, canSubmit, hasHostApproval, stateLabel, operationLabel,
    operationElapsedSeconds, operationProgress,
    enrollmentResponse, enrollmentFileName, enrollmentSetup, enrollmentRequest,
    enrollmentResponsePreview, enrollmentSetupError, enrollmentProgress,
    enrollmentResponseError, enrollmentCommand, canCopyEnrollmentCommand,
    canApplyEnrollment, copyEnrollmentCommand, prepareEnrollment,
    downloadEnrollmentRequest, loadEnrollmentResponse, applyEnrollment,
    formatDateTime, formatBytes, loadStatus, runBackup,
  }
}
