import { computed, reactive, ref, watch } from 'vue'

import { applyBackupEnrollment, prepareBackupEnrollment } from '@/modules/admin/api/admin'
import {
  buildBackupEnrollmentCommand,
  normalizeBackupEnrollmentFile,
  parseBackupEnrollmentResponse,
  validateBackupEnrollmentSetup,
} from '@/modules/admin/domain/backupEnrollment'

export function useBackupEnrollment({ status, canSubmit, error, success, request, t }) {
  const response = ref('')
  const responseFileName = ref('')
  const setup = reactive({
    host: '',
    port: 22,
    directory: '/backups/wosb',
    retentionDays: 30,
    allowFrom: '',
  })
  const enrollmentPreparationActive = computed(() => (
    status.value.operation === 'prepare_enrollment'
    && ['queued', 'running'].includes(status.value.state)
  ))
  const enrollmentRequest = computed(() => (
    enrollmentPreparationActive.value ? null : status.value.enrollment_request || null
  ))
  const requestFilename = computed(() => (
    enrollmentRequest.value
      ? `rbf-backup-enrollment-request-${enrollmentRequest.value.enrollment_id}.json`
      : 'REQUEST.json'
  ))
  const responseResult = computed(() => parseBackupEnrollmentResponse(
    response.value,
    String(enrollmentRequest.value?.enrollment_id || ''),
    String(enrollmentRequest.value?.deployment_environment || ''),
  ))
  const responsePreview = computed(() => responseResult.value.payload)
  const responseError = computed(() => {
    if (!response.value.trim() || !responseResult.value.error) return ''
    const messageKey = {
      empty: 'empty',
      invalidJson: 'invalidJson',
      invalidObject: 'invalidJson',
      unsupportedSchema: 'wrongFile',
      requestSelected: 'wrongFile',
      wrongKind: 'wrongFile',
      invalidEnrollmentId: 'invalidContent',
      enrollmentMismatch: 'enrollmentMismatch',
      invalidHost: 'invalidContent',
      invalidPort: 'invalidContent',
      invalidUsername: 'invalidContent',
      invalidRemoteDirectory: 'invalidContent',
      invalidHostKey: 'invalidContent',
      invalidFingerprint: 'invalidContent',
      invalidAgeRecipient: 'invalidContent',
      unmanagedServer: 'unmanagedServer',
    }[responseResult.value.error] || 'invalidContent'
    return t(`admin.backups.enrollment.errors.${messageKey}`)
  })
  const setupResult = computed(() => validateBackupEnrollmentSetup({
    ...setup,
    requestFilename: requestFilename.value,
    enrollmentId: enrollmentRequest.value?.enrollment_id,
    releaseVersion: enrollmentRequest.value?.release_version,
    provisionerBase64: enrollmentRequest.value?.provisioner_base64,
    provisionerSha256: enrollmentRequest.value?.provisioner_sha256,
    ingestScriptBase64: enrollmentRequest.value?.ingest_script_base64,
    ingestScriptSha256: enrollmentRequest.value?.ingest_script_sha256,
    deploymentEnvironment: enrollmentRequest.value?.deployment_environment,
    requestedUsername: enrollmentRequest.value?.requested_username,
    requestedRecoveryUsername: enrollmentRequest.value?.requested_recovery_username,
    requestedStorageDirectory: enrollmentRequest.value?.requested_storage_directory,
  }))
  const setupError = computed(() => {
    if (!setup.host.trim()) return t('admin.backups.enrollment.errors.hostRequired')
    const errorKey = ['invalidReleaseVersion', 'invalidProvisioner'].includes(setupResult.value.error)
      ? 'invalidRequestFilename'
      : setupResult.value.error
    return setupResult.value.error
      ? t(`admin.backups.enrollment.errors.${errorKey}`)
      : ''
  })
  const command = computed(() => buildBackupEnrollmentCommand({
    ...setup,
    requestFilename: requestFilename.value,
    enrollmentId: enrollmentRequest.value?.enrollment_id,
    releaseVersion: enrollmentRequest.value?.release_version,
    provisionerBase64: enrollmentRequest.value?.provisioner_base64,
    provisionerSha256: enrollmentRequest.value?.provisioner_sha256,
    ingestScriptBase64: enrollmentRequest.value?.ingest_script_base64,
    ingestScriptSha256: enrollmentRequest.value?.ingest_script_sha256,
    deploymentEnvironment: enrollmentRequest.value?.deployment_environment,
    requestedUsername: enrollmentRequest.value?.requested_username,
    requestedRecoveryUsername: enrollmentRequest.value?.requested_recovery_username,
    requestedStorageDirectory: enrollmentRequest.value?.requested_storage_directory,
  }).command)
  watch(
    () => enrollmentRequest.value?.requested_storage_directory,
    (directory) => {
      if (directory) setup.directory = String(directory)
    },
    { immediate: true },
  )
  const canCopyCommand = computed(() => (
    Boolean(enrollmentRequest.value) && !setupResult.value.error && Boolean(command.value)
  ))
  const progress = computed(() => ({
    requestCreated: Boolean(enrollmentRequest.value),
    responseSelected: Boolean(response.value.trim()),
    responseValid: Boolean(responsePreview.value),
    connectionVerified: Boolean(status.value.connection?.write_tested_at)
      && Boolean(status.value.connection?.managed_server),
  }))
  // Keep the action available while the page is idle. Its click handler can
  // then explain a missing file, mismatched response, or missing token instead
  // of presenting a disabled button with no reason.
  const canApply = computed(() => canSubmit.value)

  async function copyCommand() {
    if (!canCopyCommand.value) {
      error.value = setupError.value || t('admin.backups.enrollment.errors.createRequestFirst')
      return
    }
    try {
      await navigator.clipboard.writeText(command.value)
      success.value = t('admin.backups.messages.enrollmentCommandCopied')
      error.value = ''
    } catch {
      error.value = t('admin.backups.errors.copyEnrollmentCommand')
    }
  }

  async function prepare() {
    response.value = ''
    responseFileName.value = ''
    await request(
      (token) => prepareBackupEnrollment(token),
      'admin.backups.messages.enrollmentPrepared',
    )
  }

  function downloadRequest() {
    if (!enrollmentRequest.value) return
    const content = `${JSON.stringify(enrollmentRequest.value, null, 2)}\n`
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = requestFilename.value
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  async function loadResponse(event) {
    const input = event.target
    const [file] = input.files || []
    if (!file) return
    try {
      response.value = normalizeBackupEnrollmentFile(await file.text())
      responseFileName.value = file.name
      error.value = ''
    } catch {
      response.value = ''
      responseFileName.value = ''
      error.value = t('admin.backups.enrollment.errors.readFailed')
    } finally {
      input.value = ''
    }
  }

  async function apply() {
    if (!enrollmentRequest.value) {
      error.value = t('admin.backups.enrollment.errors.noActiveRequest')
      return
    }
    if (!response.value.trim()) {
      error.value = t('admin.backups.enrollment.errors.selectResponse')
      return
    }
    if (responseResult.value.error) {
      error.value = responseError.value
      return
    }
    await request(
      (token) => applyBackupEnrollment({ response_json: response.value.trim() }, token),
      'admin.backups.messages.enrollmentApplied',
    )
  }

  return {
    response,
    responseFileName,
    setup,
    enrollmentRequest,
    responsePreview,
    setupError,
    progress,
    responseError,
    requestFilename,
    command,
    canCopyCommand,
    canApply,
    copyCommand,
    prepare,
    downloadRequest,
    loadResponse,
    apply,
  }
}
