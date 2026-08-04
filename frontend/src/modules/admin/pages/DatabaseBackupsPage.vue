<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useDatabaseBackupsPage } from '@/modules/admin/composables/useDatabaseBackupsPage'

const {
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
  enrollmentFileName,
  enrollmentSetup,
  inProgress,
  configured,
  connectionReady,
  uploadPublicKey,
  uploadKeyFingerprint,
  canSubmit,
  canRestore,
  canRestoreFiles,
  isBootstrapAdmin,
  enrollmentRequest,
  enrollmentResponsePreview,
  enrollmentSetupError,
  enrollmentProgress,
  enrollmentResponseError,
  enrollmentCommand,
  canCopyEnrollmentCommand,
  canApplyEnrollment,
  localBackups,
  localFilesBackups,
  selectedBackup,
  selectedFilesBackup,
  filesRestoreForm,
  stateLabel,
  operationLabel,
  discoveredMatchesForm,
  formatDateTime,
  formatBytes,
  loadStatus,
  prepareUploadKey,
  copyUploadPublicKey,
  copyEnrollmentCommand,
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
  restoreFiles,
  removeConfiguration,
} = useDatabaseBackupsPage()
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('admin.backups.eyebrow')"
    :title="t('admin.backups.title')"
    :description="t('admin.backups.subtitle')"
    title-id="database-backups-title"
    :groups="navigationGroups"
    active-key="backups"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions>
      <button class="button-box" type="button" :disabled="loading" @click="loadStatus()">
        {{ t('admin.backups.actions.refresh') }}
      </button>
      <RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink>
    </template>

    <div class="backup-workspace staff-subworkspace">
      <section class="wire-section admin-panel backup-status-panel" aria-live="polite">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.statusTitle') }}</h2>
            <p>{{ status.message || t('admin.backups.statusHint') }}</p>
          </div>
          <span class="summary-pill" :class="`status-${status.state}`">{{ stateLabel }}</span>
        </div>
        <div class="backup-metric-grid">
          <article class="home-status-card refined-status-card">
            <span>{{ t('admin.backups.connection.label') }}</span>
            <strong>
              {{ configured ? t('admin.backups.connection.configured') : t('admin.backups.connection.missing') }}
            </strong>
            <p v-if="configured">
              {{ status.connection.username }}@{{ status.connection.host }}:{{ status.connection.port }}
            </p>
            <small v-if="configured">
              {{ connectionReady
                ? t('admin.backups.connection.writeVerified', { date: formatDateTime(status.connection.write_tested_at) })
                : t('admin.backups.connection.writeUnverified') }}
            </small>
            <p v-else>{{ t('admin.backups.connection.missingHint') }}</p>
          </article>
          <article class="home-status-card refined-status-card">
            <span>{{ t('admin.backups.operation') }}</span>
            <strong>{{ operationLabel }}</strong>
            <p>{{ t('admin.backups.requestedBy') }}: {{ status.requested_by || '—' }}</p>
            <small>{{ formatDateTime(status.finished_at || status.started_at || status.requested_at) }}</small>
          </article>
          <article class="home-status-card refined-status-card">
            <span>{{ t('admin.backups.lastBackup') }}</span>
            <strong>{{ status.artifacts?.length || 0 }}</strong>
            <p>
              {{ status.artifacts?.length
                ? t('admin.backups.artifactCount', { count: status.artifacts.length })
                : t('admin.backups.noBackup') }}
            </p>
            <small>{{ t('admin.backups.backupCoverage') }}</small>
          </article>
        </div>
        <p v-if="success" class="success-text table-state">{{ success }}</p>
        <p v-if="error" class="error-text table-state">{{ error }}</p>
      </section>


      <section class="wire-section admin-panel backup-configuration-panel backup-enrollment-wizard">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.enrollment.title') }}</h2>
            <p>{{ t('admin.backups.enrollment.subtitle') }}</p>
          </div>
          <span class="summary-pill">{{ t('admin.backups.enrollment.recommended') }}</span>
        </div>

        <ol class="backup-setup-progress" :aria-label="t('admin.backups.enrollment.progressTitle')">
          <li :class="{ 'is-complete': enrollmentProgress.requestCreated }">
            <span>1</span>
            <strong>{{ t('admin.backups.enrollment.progress.request') }}</strong>
          </li>
          <li :class="{ 'is-complete': enrollmentProgress.responseSelected }">
            <span>2</span>
            <strong>{{ t('admin.backups.enrollment.progress.provision') }}</strong>
          </li>
          <li :class="{ 'is-complete': enrollmentProgress.responseValid }">
            <span>3</span>
            <strong>{{ t('admin.backups.enrollment.progress.response') }}</strong>
          </li>
          <li :class="{ 'is-complete': enrollmentProgress.connectionVerified }">
            <span>4</span>
            <strong>{{ t('admin.backups.enrollment.progress.verified') }}</strong>
          </li>
        </ol>

        <div class="backup-security-note">
          <strong>{{ t('admin.backups.enrollment.securityTitle') }}</strong>
          <p>{{ t('admin.backups.enrollment.securityText') }}</p>
          <small>{{ t('admin.backups.enrollment.noPrivateKey') }}</small>
        </div>

        <div class="backup-configuration-form backup-enrollment-steps">
          <section class="input-panel embedded-field backup-directory-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepOne') }}</span>
            <p>{{ t('admin.backups.enrollment.stepOneText') }}</p>
            <div class="backup-form-actions">
              <button class="form-button primary-action" type="button" :disabled="!canSubmit" @click="prepareEnrollment">
                {{ t('admin.backups.actions.prepareEnrollment') }}
              </button>
              <button class="form-button secondary-action" type="button" :disabled="!enrollmentRequest" @click="downloadEnrollmentRequest">
                {{ t('admin.backups.actions.downloadEnrollment') }}
              </button>
            </div>
            <div v-if="enrollmentRequest" class="backup-setup-result">
              <strong>{{ t('admin.backups.enrollment.requestReady') }}</strong>
              <code class="backup-checksum">{{ enrollmentRequest.enrollment_id }}</code>
              <small>{{ t('admin.backups.enrollment.requestFilenameHint') }}</small>
            </div>
          </section>

          <section class="input-panel embedded-field backup-directory-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepTwo') }}</span>
            <p>{{ t('admin.backups.enrollment.stepTwoText') }}</p>
            <div class="backup-enrollment-command-fields">
              <label>
                <span>{{ t('admin.backups.enrollment.commandFields.host') }}</span>
                <input v-model.trim="enrollmentSetup.host" placeholder="192.168.2.107" maxlength="253" />
              </label>
              <label>
                <span>{{ t('admin.backups.enrollment.commandFields.port') }}</span>
                <input v-model.number="enrollmentSetup.port" type="number" min="1" max="65535" />
              </label>
              <label>
                <span>{{ t('admin.backups.enrollment.commandFields.directory') }}</span>
                <input v-model.trim="enrollmentSetup.directory" placeholder="/srv/rbf-backups/wosb" maxlength="512" />
              </label>
              <label>
                <span>{{ t('admin.backups.enrollment.commandFields.retention') }}</span>
                <input v-model.number="enrollmentSetup.retentionDays" type="number" min="1" max="3650" />
              </label>
              <label class="backup-enrollment-wide-field">
                <span>{{ t('admin.backups.enrollment.commandFields.allowFrom') }}</span>
                <input v-model.trim="enrollmentSetup.allowFrom" placeholder="192.168.2.36/32" maxlength="64" />
                <small>{{ t('admin.backups.enrollment.commandFields.allowFromHint') }}</small>
              </label>
            </div>
            <p v-if="enrollmentSetupError" class="error-text backup-enrollment-validation">
              {{ enrollmentSetupError }}
            </p>
            <div class="backup-command-panel">
              <pre><code>{{ enrollmentCommand || t('admin.backups.enrollment.commandPlaceholder') }}</code></pre>
              <button
                class="small-action"
                type="button"
                :disabled="!canCopyEnrollmentCommand"
                @click="copyEnrollmentCommand"
              >
                {{ t('admin.backups.actions.copyEnrollmentCommand') }}
              </button>
            </div>
            <small>{{ t('admin.backups.enrollment.commandHint') }}</small>
          </section>

          <section class="input-panel embedded-field backup-private-key-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepThree') }}</span>
            <p>{{ t('admin.backups.enrollment.stepThreeText') }}</p>
            <input type="file" accept="application/json,.json" :disabled="!canSubmit" @change="loadEnrollmentResponse" />
            <small v-if="enrollmentFileName">{{ t('admin.backups.enrollment.selectedFile', { filename: enrollmentFileName }) }}</small>
            <details class="backup-response-paste">
              <summary>{{ t('admin.backups.enrollment.pasteFallback') }}</summary>
              <textarea
                v-model="enrollmentResponse"
                rows="7"
                spellcheck="false"
                autocomplete="off"
                :placeholder="t('admin.backups.enrollment.responsePlaceholder')"
              />
            </details>
            <p v-if="enrollmentResponseError" class="error-text backup-enrollment-validation">
              {{ enrollmentResponseError }}
            </p>
            <div v-else-if="enrollmentResponsePreview" class="backup-host-key-panel backup-enrollment-preview">
              <div>
                <span>{{ enrollmentResponsePreview.username }}@{{ enrollmentResponsePreview.host }}:{{ enrollmentResponsePreview.port }}</span>
                <strong>{{ enrollmentResponsePreview.host_key_fingerprint }}</strong>
                <small>{{ t('admin.backups.enrollment.compareFingerprint') }}</small>
              </div>
            </div>
            <div class="backup-form-actions">
              <button class="form-button primary-action" type="button" :disabled="!canApplyEnrollment" @click="applyEnrollment">
                {{ t('admin.backups.actions.applyEnrollment') }}
              </button>
              <small v-if="!enrollmentRequest">{{ t('admin.backups.enrollment.errors.noActiveRequest') }}</small>
              <small v-else-if="!enrollmentResponse.trim()">{{ t('admin.backups.enrollment.errors.selectResponse') }}</small>
              <small v-else-if="enrollmentResponseError">{{ enrollmentResponseError }}</small>
              <small v-else>{{ t('admin.backups.enrollment.responseReady') }}</small>
            </div>
          </section>

          <section v-if="enrollmentProgress.connectionVerified" class="backup-setup-complete">
            <strong>{{ t('admin.backups.enrollment.completeTitle') }}</strong>
            <p>{{ t('admin.backups.enrollment.completeText') }}</p>
          </section>
        </div>
      </section>

      <details
        class="wire-section admin-panel backup-configuration-panel backup-manual-setup"
        :open="configured && !status.connection?.managed_server"
      >
        <summary class="admin-panel-heading backup-manual-summary">
          <div>
            <h2>{{ t('admin.backups.configuration.title') }}</h2>
            <p>{{ t('admin.backups.configuration.subtitle') }}</p>
          </div>
          <span class="summary-pill">{{ t('admin.backups.configuration.advanced') }}</span>
        </summary>
        <div class="backup-security-note">
          <strong>{{ t('admin.backups.security.title') }}</strong>
          <p>{{ t('admin.backups.security.text') }}</p>
        </div>
        <div class="backup-security-note backup-upload-key-note">
          <strong>{{ t('admin.backups.uploadKey.title') }}</strong>
          <p>{{ t('admin.backups.uploadKey.text') }}</p>
          <div class="backup-form-actions">
            <button class="form-button secondary-action" type="button" :disabled="!canSubmit" @click="prepareUploadKey">
              {{ t('admin.backups.actions.prepareKey') }}
            </button>
            <button class="small-action" type="button" :disabled="!uploadPublicKey" @click="copyUploadPublicKey">
              {{ t('admin.backups.actions.copyPublicKey') }}
            </button>
          </div>
          <code v-if="uploadPublicKey" class="backup-public-key">{{ uploadPublicKey }}</code>
          <small v-if="uploadKeyFingerprint">{{ t('admin.backups.uploadKey.fingerprint') }}: {{ uploadKeyFingerprint }}</small>
        </div>
        <form class="backup-configuration-form" @submit.prevent="saveConfiguration">
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.fields.host') }}</span>
            <input v-model.trim="form.host" required maxlength="253" placeholder="backup.example.net" />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.fields.port') }}</span>
            <input v-model.number="form.port" required type="number" min="1" max="65535" />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.fields.username') }}</span>
            <input v-model.trim="form.username" required maxlength="64" autocomplete="username" />
          </label>
          <label class="input-panel embedded-field backup-directory-field">
            <span>{{ t('admin.backups.fields.remoteDirectory') }}</span>
            <input
              v-model.trim="form.remote_directory"
              required
              maxlength="512"
              placeholder="/data"
            />
            <small>{{ t('admin.backups.remoteDirectoryHint') }}</small>
          </label>
          <div class="backup-host-key-panel">
            <div>
              <span>{{ t('admin.backups.fields.hostKey') }}</span>
              <strong>{{ status.discovered_fingerprint || status.connection?.host_key_fingerprint || '—' }}</strong>
              <small>
                {{ discoveredMatchesForm
                  ? t('admin.backups.hostKeyReady')
                  : t('admin.backups.hostKeyHint') }}
              </small>
            </div>
            <button
              class="small-action"
              type="button"
              :disabled="!canSubmit || !form.host"
              @click="discover"
            >
              {{ t('admin.backups.actions.discover') }}
            </button>
          </div>
          <label class="input-panel embedded-field backup-private-key-field">
            <span>{{ t('admin.backups.fields.privateKey') }}</span>
            <small>{{ t('admin.backups.privateKeyHint') }}</small>
            <textarea
              v-model="form.private_key"
              :class="{ 'is-concealed': !privateKeyVisible }"
              rows="8"
              spellcheck="false"
              autocomplete="off"
              :placeholder="status.connection?.private_key_configured
                ? t('admin.backups.privateKeyKeep')
                : t('admin.backups.privateKeyPlaceholder')"
            />
            <button
              class="small-action backup-key-toggle"
              type="button"
              @click="privateKeyVisible = !privateKeyVisible"
            >
              {{ privateKeyVisible
                ? t('admin.backups.actions.hideKey')
                : t('admin.backups.actions.showKey') }}
            </button>
          </label>
          <div class="backup-form-actions">
            <button
              class="form-button primary-action"
              type="submit"
              :disabled="!canSubmit || !discoveredMatchesForm"
            >
              {{ t('admin.backups.actions.saveAndTest') }}
            </button>
            <button
              class="form-button secondary-action"
              type="button"
              :disabled="!canSubmit || !configured"
              @click="testConnection"
            >
              {{ t('admin.backups.actions.test') }}
            </button>
            <button
              class="danger-action"
              type="button"
              :disabled="!canSubmit || !configured"
              @click="removeConfiguration"
            >
              {{ t('admin.backups.actions.delete') }}
            </button>
          </div>
        </form>
      </details>

      <section class="wire-section admin-panel backup-run-panel">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.run.title') }}</h2>
            <p>{{ t('admin.backups.run.subtitle') }}</p>
          </div>
          <button
            class="form-button primary-action"
            type="button"
            :disabled="!canSubmit || !connectionReady"
            @click="runBackup"
          >
            {{ inProgress ? t('admin.backups.actions.running') : t('admin.backups.actions.run') }}
          </button>
        </div>
        <div v-if="status.artifacts?.length" class="backup-artifact-list">
          <article
            v-for="artifact in status.artifacts"
            :key="artifact.remote_path"
            class="home-status-card refined-status-card backup-artifact-card"
          >
            <span>{{ t(`admin.backups.artifacts.${artifact.artifact_type}`) }}</span>
            <strong>{{ artifact.filename }}</strong>
            <p>{{ formatBytes(artifact.size_bytes) }}</p>
            <dl class="system-update-meta backup-result-meta">
              <div>
                <dt>{{ t('admin.backups.remotePath') }}</dt>
                <dd>{{ artifact.remote_path }}</dd>
              </div>
              <div>
                <dt>{{ t('admin.backups.checksum') }}</dt>
                <dd class="backup-checksum">{{ artifact.sha256 }}</dd>
              </div>
            </dl>
          </article>
        </div>
        <p v-else class="muted">{{ t('admin.backups.noBackup') }}</p>
      </section>

      <section class="wire-section admin-panel backup-restore-panel">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.restore.title') }}</h2>
            <p>{{ t('admin.backups.restore.subtitle') }}</p>
          </div>
          <button
            class="form-button secondary-action"
            type="button"
            :disabled="!canSubmit"
            @click="scanLocalBackups"
          >
            {{ t('admin.backups.actions.scanLocal') }}
          </button>
        </div>

        <div class="backup-security-note backup-restore-warning">
          <strong>{{ t('admin.backups.restore.securityTitle') }}</strong>
          <p>{{ t('admin.backups.restore.securityText') }}</p>
          <code>sudo ./infrastructure/scripts/backup/arm-admin-restore.sh</code>
        </div>

        <div class="backup-catalog-meta">
          <span>
            {{ t('admin.backups.restore.catalogUpdated') }}:
            {{ formatDateTime(status.local_catalog_updated_at) }}
          </span>
          <span v-if="status.local_catalog_skipped_count">
            {{ t('admin.backups.restore.skipped', { count: status.local_catalog_skipped_count }) }}
          </span>
        </div>

        <div v-if="localBackups.length" class="backup-local-catalog">
          <label
            v-for="backup in localBackups"
            :key="backup.backup_id"
            class="backup-local-entry"
            :class="{ 'is-selected': restoreForm.backup_id === backup.backup_id }"
          >
            <input
              v-model="restoreForm.backup_id"
              type="radio"
              name="database-backup"
              :value="backup.backup_id"
              :disabled="!isBootstrapAdmin || inProgress || !backup.restore_metadata_verified || !backup.production_consistent || !backup.backup_set_verified || backup.encryption_keys_compatible === false"
            />
            <span class="backup-local-entry-main">
              <strong>{{ backup.filename }}</strong>
              <small>{{ formatDateTime(backup.created_at) }} · {{ formatBytes(backup.size_bytes) }}</small>
              <small v-if="backup.flyway_version">{{ t('admin.backups.restore.schemaRevision') }}: {{ backup.flyway_version }}</small>
              <small v-if="!backup.restore_metadata_verified" class="backup-compatibility is-incompatible">
                {{ t('admin.backups.restore.metadataMissing') }}
              </small>
              <small v-else-if="!backup.production_consistent" class="backup-compatibility is-incompatible">
                {{ t('admin.backups.restore.uncoordinated') }}
              </small>
              <small v-else-if="!backup.backup_set_verified" class="backup-compatibility is-incompatible">
                {{ t('admin.backups.restore.backupSetMissing') }}
              </small>
              <small v-else class="backup-compatibility">
                {{ t('admin.backups.restore.recoveryVerified') }}
              </small>
              <small
                class="backup-compatibility"
                :class="{ 'is-incompatible': backup.encryption_keys_compatible === false }"
              >
                {{ backup.encryption_keys_compatible === true
                  ? t('admin.backups.restore.keysCompatible')
                  : backup.encryption_keys_compatible === false
                    ? t('admin.backups.restore.keysIncompatible')
                    : t('admin.backups.restore.keysUnknown') }}
              </small>
            </span>
            <span class="backup-checksum backup-local-checksum">{{ backup.sha256 }}</span>
          </label>
        </div>
        <p v-else class="muted">{{ t('admin.backups.restore.empty') }}</p>

        <form
          v-if="isBootstrapAdmin"
          class="backup-restore-form"
          @submit.prevent="restoreDatabase"
        >
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.restore.approvalToken') }}</span>
            <input
              v-model.trim="restoreForm.approval_token"
              type="password"
              minlength="24"
              maxlength="128"
              autocomplete="off"
              spellcheck="false"
              :placeholder="t('admin.backups.restore.approvalPlaceholder')"
            />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.restore.confirmation') }}</span>
            <input
              v-model="restoreForm.confirmation"
              autocomplete="off"
              spellcheck="false"
              placeholder="RESTORE DATABASE"
            />
          </label>
          <div class="backup-restore-selection">
            <span>{{ t('admin.backups.restore.selected') }}</span>
            <strong>{{ selectedBackup?.filename || '—' }}</strong>
          </div>
          <button class="danger-action" type="submit" :disabled="!canRestore">
            {{ inProgress
              ? t('admin.backups.actions.running')
              : t('admin.backups.actions.restoreDatabase') }}
          </button>
        </form>
        <p v-else class="backup-bootstrap-only">
          {{ t('admin.backups.restore.bootstrapOnly') }}
        </p>
      </section>

      <section class="wire-section admin-panel backup-restore-panel">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.restore.filesTitle') }}</h2>
            <p>{{ t('admin.backups.restore.filesSubtitle') }}</p>
          </div>
        </div>
        <div v-if="localFilesBackups.length" class="backup-local-catalog">
          <label
            v-for="backup in localFilesBackups"
            :key="backup.backup_id"
            class="backup-local-entry"
            :class="{ 'is-selected': filesRestoreForm.backup_id === backup.backup_id }"
          >
            <input
              v-model="filesRestoreForm.backup_id"
              type="radio"
              name="files-backup"
              :value="backup.backup_id"
              :disabled="!isBootstrapAdmin || inProgress"
            />
            <span class="backup-local-entry-main">
              <strong>{{ backup.filename }}</strong>
              <small>{{ formatDateTime(backup.created_at) }} · {{ formatBytes(backup.size_bytes) }}</small>
              <small>{{ t('admin.backups.restore.modulesAvailable') }}: {{ backup.components.join(', ') }}</small>
            </span>
            <span class="backup-checksum backup-local-checksum">{{ backup.sha256 }}</span>
          </label>
        </div>
        <p v-else class="muted">{{ t('admin.backups.restore.filesEmpty') }}</p>
        <form v-if="isBootstrapAdmin" class="backup-restore-form" @submit.prevent="restoreFiles">
          <fieldset class="backup-module-selection">
            <legend>{{ t('admin.backups.restore.modules') }}</legend>
            <label v-for="module in ['uploads', 'certs', 'letsencrypt']" :key="module">
              <input
                v-model="filesRestoreForm.components"
                type="checkbox"
                :value="module"
                :disabled="!selectedFilesBackup?.components.includes(module) || inProgress"
              />
              <span>{{ t(`admin.backups.restore.moduleLabels.${module}`) }}</span>
            </label>
          </fieldset>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.restore.approvalToken') }}</span>
            <input v-model.trim="filesRestoreForm.approval_token" type="password" minlength="24" maxlength="128" autocomplete="off" />
          </label>
          <label class="input-panel embedded-field">
            <span>{{ t('admin.backups.restore.filesConfirmation') }}</span>
            <input v-model="filesRestoreForm.confirmation" autocomplete="off" placeholder="RESTORE FILES" />
          </label>
          <button class="danger-action" type="submit" :disabled="!canRestoreFiles">
            {{ inProgress ? t('admin.backups.actions.running') : t('admin.backups.actions.restoreFiles') }}
          </button>
        </form>
        <p v-else class="backup-bootstrap-only">{{ t('admin.backups.restore.bootstrapOnly') }}</p>
      </section>

      <div class="backup-host-log-note">
        {{ t('admin.backups.hostLogOnly') }}
      </div>
    </div>
  </StaffWorkspaceShell>
</template>
