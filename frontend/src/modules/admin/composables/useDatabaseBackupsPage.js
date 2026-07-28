import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  configureBackupConnection,
  deleteBackupConnection,
  discoverBackupHost,
  getBackupControlStatus,
  runDatabaseBackup,
  testBackupConnection,
} from '@/modules/admin/api/admin'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const EMPTY_STATUS = {
  state: 'idle',
  operation: 'idle',
  message: '',
  connection: { configured: false, private_key_configured: false },
  log_tail: [],
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
  const privateKeyVisible = ref(false)
  const logOpen = ref(false)
  const form = reactive({
    host: '',
    port: 22,
    username: '',
    remote_directory: '/backups/royal-blackwater-fleet',
    private_key: '',
    host_key: '',
  })
  let pollTimer = null

  const inProgress = computed(() => ['queued', 'running'].includes(status.value.state))
  const configured = computed(() => Boolean(status.value.connection?.configured))
  const canSubmit = computed(() => !loading.value && !inProgress.value && status.value.request_available !== false)
  const stateLabel = computed(() => t(`admin.backups.states.${status.value.state || 'idle'}`))
  const operationLabel = computed(() => t(`admin.backups.operations.${status.value.operation || 'idle'}`))
  const discoveredMatchesForm = computed(() => (
    status.value.discovered_host === form.host.trim()
    && Number(status.value.discovered_port) === Number(form.port)
    && Boolean(status.value.discovered_host_key)
  ))

  function formatDateTime(value) {
    if (!value) return '—'
    return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
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
      status.value = await getBackupControlStatus()
      hydrateForm()
      if (status.value.operation === 'discover' && status.value.state === 'succeeded') {
        form.host_key = status.value.discovered_host_key || ''
      }
      if (previousState && ['queued', 'running'].includes(previousState) && status.value.state === 'succeeded') {
        success.value = status.value.message
        if (status.value.operation === 'configure') form.private_key = ''
      }
      if (status.value.state === 'failed') error.value = status.value.message
    } catch (err) {
      error.value = err.message || t('admin.backups.errors.load')
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
    await request(runDatabaseBackup, 'admin.backups.messages.backupQueued')
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
    privateKeyVisible,
    logOpen,
    inProgress,
    configured,
    canSubmit,
    stateLabel,
    operationLabel,
    discoveredMatchesForm,
    formatDateTime,
    formatBytes,
    loadStatus,
    discover,
    saveConfiguration,
    testConnection,
    runBackup,
    removeConfiguration,
  }
}
