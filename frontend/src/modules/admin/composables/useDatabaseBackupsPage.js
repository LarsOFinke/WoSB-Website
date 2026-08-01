import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  applyBackupEnrollment,
  configureBackupConnection,
  deleteBackupConnection,
  discoverBackupHost,
  getBackupControlStatus,
  prepareBackupEnrollment,
  restoreLocalDatabaseBackup,
  runApplicationBackup,
  scanLocalDatabaseBackups,
  testBackupConnection,
} from '@/modules/admin/api/admin'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const EMPTY_STATUS = {
  state: 'idle',
  operation: 'idle',
  message: '',
  connection: { configured: false, private_key_configured: false },
  artifacts: [],
  local_database_backups: [],
  local_catalog_updated_at: null,
  local_catalog_skipped_count: 0,
  request_available: false,
}

const APPROVAL_TOKEN_PATTERN = /^[A-Za-z0-9_-]{24,128}$/
const RESTORE_CONFIRMATION = 'RESTORE DATABASE'

export function useDatabaseBackupsPage() {
  const { locale, t } = useLocale()
  const { isAdmin, user } = useSession()
  const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
  const status = ref({ ...EMPTY_STATUS })
  const loading = ref(false)
  const error = ref('')
  const success = ref('')
  const privateKeyVisible = ref(false)
  const enrollmentResponse = ref('')
  const form = reactive({
    host: '',
    port: 22,
    username: '',
    remote_directory: '/backups/royal-blackwater-fleet',
    private_key: '',
    host_key: '',
  })
  const restoreForm = reactive({
    backup_id: '',
    approval_token: '',
    confirmation: '',
  })
  let pollTimer = null

  const inProgress = computed(() => ['queued', 'running'].includes(status.value.state))
  const configured = computed(() => Boolean(status.value.connection?.configured))
  const canSubmit = computed(() => (
    !loading.value && !inProgress.value && status.value.request_available !== false
  ))
  const isBootstrapAdmin = computed(() => Boolean(user.value?.is_bootstrap_admin))
  const enrollmentRequest = computed(() => status.value.enrollment_request || null)
  const enrollmentResponsePreview = computed(() => {
    try {
      const payload = JSON.parse(enrollmentResponse.value)
      return payload?.kind === 'rbf-backup-enrollment-response' ? payload : null
    } catch {
      return null
    }
  })
  const canApplyEnrollment = computed(() => canSubmit.value && Boolean(enrollmentResponsePreview.value))
  const localBackups = computed(() => status.value.local_database_backups || [])
  const selectedBackup = computed(() => (
    localBackups.value.find((backup) => backup.backup_id === restoreForm.backup_id) || null
  ))
  const canRestore = computed(() => (
    canSubmit.value
    && isBootstrapAdmin.value
    && Boolean(selectedBackup.value)
    && selectedBackup.value?.restore_metadata_verified === true
    && selectedBackup.value?.production_consistent === true
    && selectedBackup.value?.backup_set_verified === true
    && selectedBackup.value?.encryption_keys_compatible !== false
    && APPROVAL_TOKEN_PATTERN.test(restoreForm.approval_token.trim())
    && restoreForm.confirmation === RESTORE_CONFIRMATION
  ))
  const stateLabel = computed(() => t(`admin.backups.states.${status.value.state || 'idle'}`))
  const operationLabel = computed(() => (
    t(`admin.backups.operations.${status.value.operation || 'idle'}`)
  ))
  const discoveredMatchesForm = computed(() => (
    status.value.discovered_host === form.host.trim()
    && Number(status.value.discovered_port) === Number(form.port)
    && Boolean(status.value.discovered_host_key)
  ))

  function formatDateTime(value) {
    if (!value) return '—'
    return new Intl.DateTimeFormat(locale.value, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  }

  function formatBytes(value) {
    const size = Number(value || 0)
    if (!size) return '—'
    if (size < 1024) return `${size} B`
    if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`
    if (size < 1024 ** 3) return `${(size / 1024 ** 2).toFixed(1)} MB`
    return `${(size / 1024 ** 3).toFixed(2)} GB`
  }

  function hydrateForm() {
    const connection = status.value.connection || {}
    if (!connection.configured) return
    form.host = connection.host || form.host
    form.port = connection.port || form.port
    form.username = connection.username || form.username
    form.remote_directory = connection.remote_directory || form.remote_directory
  }

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
      const previousOperation = status.value.operation
      status.value = await getBackupControlStatus()
      hydrateForm()
      if (status.value.operation === 'discover' && status.value.state === 'succeeded') {
        form.host_key = status.value.discovered_host_key || ''
      }
      if (previousState && ['queued', 'running'].includes(previousState)
        && status.value.state === 'succeeded') {
        success.value = status.value.message
        if (status.value.operation === 'configure') form.private_key = ''
        if (previousOperation === 'restore_postgresql') {
          restoreForm.approval_token = ''
          restoreForm.confirmation = ''
        }
      }
      if (status.value.state === 'failed') error.value = status.value.message
    } catch (err) {
      const expectedRestoreRestart = quiet
        && status.value.operation === 'restore_postgresql'
        && inProgress.value
      if (!expectedRestoreRestart) error.value = err.message || t('admin.backups.errors.load')
    } finally {
      if (!quiet) loading.value = false
    }
  }

  async function request(action, successKey) {
    if (!canSubmit.value) return
    loading.value = true
    error.value = ''
    success.value = ''
    try {
      const response = await action()
      status.value = response.status
      success.value = t(successKey)
      schedulePoll()
    } catch (err) {
      error.value = err.message || t('admin.backups.errors.request')
    } finally {
      loading.value = false
    }
  }

  async function prepareEnrollment() {
    await request(prepareBackupEnrollment, 'admin.backups.messages.enrollmentPrepared')
  }

  function downloadEnrollmentRequest() {
    if (!enrollmentRequest.value) return
    const content = `${JSON.stringify(enrollmentRequest.value, null, 2)}\n`
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rbf-backup-enrollment-${enrollmentRequest.value.enrollment_id}.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function loadEnrollmentResponse(event) {
    const [file] = event.target.files || []
    if (!file) return
    enrollmentResponse.value = await file.text()
  }

  async function applyEnrollment() {
    if (!enrollmentResponse.value.trim()) return
    await request(
      () => applyBackupEnrollment({ response_json: enrollmentResponse.value.trim() }),
      'admin.backups.messages.enrollmentApplied',
    )
    enrollmentResponse.value = ''
  }

  async function discover() {
    form.host_key = ''
    await request(
      () => discoverBackupHost({ host: form.host, port: Number(form.port) }),
      'admin.backups.messages.discoveryQueued',
    )
  }

  async function saveConfiguration() {
    if (!discoveredMatchesForm.value) {
      error.value = t('admin.backups.errors.discoverFirst')
      return
    }
    if (!form.private_key.trim() && !status.value.connection?.private_key_configured) {
      error.value = t('admin.backups.errors.privateKeyRequired')
      return
    }
    await request(
      () => configureBackupConnection({
        host: form.host,
        port: Number(form.port),
        username: form.username,
        remote_directory: form.remote_directory,
        private_key: form.private_key.trim() || null,
        host_key: form.host_key,
      }),
      'admin.backups.messages.configurationQueued',
    )
  }

  async function testConnection() {
    await request(testBackupConnection, 'admin.backups.messages.testQueued')
  }

  async function runBackup() {
    if (!window.confirm(t('admin.backups.confirmRun'))) return
    await request(runApplicationBackup, 'admin.backups.messages.backupQueued')
  }

  async function scanLocalBackups() {
    await request(scanLocalDatabaseBackups, 'admin.backups.messages.scanQueued')
  }

  async function restoreDatabase() {
    if (!canRestore.value) return
    const filename = selectedBackup.value?.filename || ''
    if (!window.confirm(t('admin.backups.restore.finalConfirm', { filename }))) return
    await request(
      () => restoreLocalDatabaseBackup({
        backup_id: restoreForm.backup_id,
        approval_token: restoreForm.approval_token.trim(),
        confirmation: restoreForm.confirmation,
      }),
      'admin.backups.messages.restoreQueued',
    )
  }

  async function removeConfiguration() {
    if (!window.confirm(t('admin.backups.confirmDelete'))) return
    await request(deleteBackupConnection, 'admin.backups.messages.deleteQueued')
  }

  onMounted(async () => {
    await loadStatus()
    schedulePoll()
  })
  onUnmounted(() => window.clearTimeout(pollTimer))

  return {
    t,
    isAdmin,
    user,
    navigationGroups,
    status,
    loading,
    error,
    success,
    form,
    restoreForm,
    privateKeyVisible,
    enrollmentResponse,
    inProgress,
    configured,
    canSubmit,
    canRestore,
    isBootstrapAdmin,
    enrollmentRequest,
    enrollmentResponsePreview,
    canApplyEnrollment,
    localBackups,
    selectedBackup,
    stateLabel,
    operationLabel,
    discoveredMatchesForm,
    formatDateTime,
    formatBytes,
    loadStatus,
    prepareEnrollment,
    downloadEnrollmentRequest,
    loadEnrollmentResponse,
    applyEnrollment,
    discover,
    saveConfiguration,
    testConnection,
    runBackup,
    scanLocalBackups,
    restoreDatabase,
    removeConfiguration,
  }
}
