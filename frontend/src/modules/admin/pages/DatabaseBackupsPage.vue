<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import HostCapabilityField from '@/modules/admin/components/HostCapabilityField.vue'
import { useDatabaseBackupsPage } from '@/modules/admin/composables/useDatabaseBackupsPage'

const {
  t, isAdmin, user, navigationGroups, status, loading, error, success, hostApproval,
  inProgress, configured, connectionReady, canSubmit, hasHostApproval, stateLabel, operationLabel,
  enrollmentFileName, enrollmentSetup, enrollmentRequest,
  enrollmentResponsePreview, enrollmentSetupError, enrollmentProgress,
  enrollmentResponseError, enrollmentCommand, canCopyEnrollmentCommand,
  canApplyEnrollment, copyEnrollmentCommand, prepareEnrollment,
  downloadEnrollmentRequest, loadEnrollmentResponse, applyEnrollment,
  formatDateTime, formatBytes, loadStatus, runBackup,
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
            <strong>{{ configured ? t('admin.backups.connection.configured') : t('admin.backups.connection.missing') }}</strong>
            <p v-if="configured">{{ status.connection.username }}@{{ status.connection.host }}:{{ status.connection.port }}</p>
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
            <p>{{ status.artifacts?.length ? t('admin.backups.artifactCount', { count: status.artifacts.length }) : t('admin.backups.noBackup') }}</p>
            <small>{{ t('admin.backups.backupCoverage') }}</small>
          </article>
        </div>
        <p v-if="success" class="success-text table-state">{{ success }}</p>
        <p v-if="error" class="error-text table-state">{{ error }}</p>
      </section>

      <section v-if="!connectionReady" class="wire-section admin-panel backup-configuration-panel backup-enrollment-wizard">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.enrollment.title') }}</h2>
            <p>{{ t('admin.backups.enrollment.subtitle') }}</p>
          </div>
          <span class="summary-pill">{{ t('admin.backups.enrollment.recommended') }}</span>
        </div>

        <ol class="backup-setup-progress" :aria-label="t('admin.backups.enrollment.progressTitle')">
          <li :class="{ 'is-complete': enrollmentProgress.requestCreated }">
            <span>1</span><strong>{{ t('admin.backups.enrollment.progress.request') }}</strong>
          </li>
          <li :class="{ 'is-complete': enrollmentProgress.responseSelected }">
            <span>2</span><strong>{{ t('admin.backups.enrollment.progress.provision') }}</strong>
          </li>
          <li :class="{ 'is-complete': enrollmentProgress.connectionVerified }">
            <span>3</span><strong>{{ t('admin.backups.enrollment.progress.verified') }}</strong>
          </li>
        </ol>

        <div class="backup-security-note">
          <strong>{{ t('admin.backups.enrollment.automaticTitle') }}</strong>
          <p>{{ t('admin.backups.enrollment.automaticText') }}</p>
        </div>

        <div class="backup-configuration-form backup-enrollment-steps">
          <section class="input-panel embedded-field backup-directory-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepOne') }}</span>
            <p>{{ t('admin.backups.enrollment.stepOneText') }}</p>
            <HostCapabilityField v-model="hostApproval" operation="prepare_enrollment" />
            <div class="backup-form-actions">
              <button class="form-button primary-action" type="button" :disabled="!canSubmit || !hasHostApproval" @click="prepareEnrollment">
                {{ t('admin.backups.actions.prepareEnrollment') }}
              </button>
              <button class="form-button secondary-action" type="button" :disabled="!enrollmentRequest" @click="downloadEnrollmentRequest">
                {{ t('admin.backups.actions.downloadEnrollment') }}
              </button>
            </div>
            <small v-if="enrollmentRequest">{{ t('admin.backups.enrollment.requestFilenameHint') }}</small>
          </section>

          <section class="input-panel embedded-field backup-directory-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepTwo') }}</span>
            <p>{{ t('admin.backups.enrollment.stepTwoText') }}</p>
            <label>
              <span>{{ t('admin.backups.enrollment.commandFields.host') }}</span>
              <input v-model.trim="enrollmentSetup.host" placeholder="backup.example.net" maxlength="253" />
            </label>
            <details>
              <summary>{{ t('admin.backups.enrollment.advanced') }}</summary>
              <div class="backup-enrollment-command-fields">
                <label>
                  <span>{{ t('admin.backups.enrollment.commandFields.port') }}</span>
                  <input v-model.number="enrollmentSetup.port" type="number" min="1" max="65535" />
                </label>
                <label>
                  <span>{{ t('admin.backups.enrollment.commandFields.retention') }}</span>
                  <input v-model.number="enrollmentSetup.retentionDays" type="number" min="1" max="3650" />
                </label>
                <label class="backup-enrollment-wide-field">
                  <span>{{ t('admin.backups.enrollment.commandFields.directory') }}</span>
                  <input v-model.trim="enrollmentSetup.directory" maxlength="512" />
                </label>
                <label class="backup-enrollment-wide-field">
                  <span>{{ t('admin.backups.enrollment.commandFields.allowFrom') }}</span>
                  <input v-model.trim="enrollmentSetup.allowFrom" maxlength="64" />
                </label>
              </div>
            </details>
            <p v-if="enrollmentSetupError" class="error-text backup-enrollment-validation">{{ enrollmentSetupError }}</p>
            <strong>{{ t('admin.backups.restore.backupServerCommandTarget') }}</strong>
            <div class="backup-command-panel">
              <pre><code>{{ enrollmentCommand || t('admin.backups.enrollment.commandPlaceholder') }}</code></pre>
              <button class="small-action" type="button" :disabled="!canCopyEnrollmentCommand" @click="copyEnrollmentCommand">
                {{ t('admin.backups.actions.copyEnrollmentCommand') }}
              </button>
            </div>
            <small>{{ t('admin.backups.enrollment.commandHint') }}</small>
          </section>

          <section class="input-panel embedded-field backup-private-key-field backup-setup-step">
            <span>{{ t('admin.backups.enrollment.stepThree') }}</span>
            <p>{{ t('admin.backups.enrollment.stepThreeText') }}</p>
            <input class="backup-enrollment-file-input" type="file" accept="application/json,.json" :disabled="!canSubmit" @change="loadEnrollmentResponse" />
            <small v-if="enrollmentFileName">{{ t('admin.backups.enrollment.selectedFile', { filename: enrollmentFileName }) }}</small>
            <p v-if="enrollmentResponseError" class="error-text backup-enrollment-validation">{{ enrollmentResponseError }}</p>
            <div v-else-if="enrollmentResponsePreview" class="backup-host-key-panel backup-enrollment-preview">
              <div>
                <span>{{ enrollmentResponsePreview.username }}@{{ enrollmentResponsePreview.host }}:{{ enrollmentResponsePreview.port }}</span>
                <strong>{{ enrollmentResponsePreview.host_key_fingerprint }}</strong>
                <small>{{ t('admin.backups.enrollment.compareFingerprint') }}</small>
              </div>
            </div>
            <HostCapabilityField v-model="hostApproval" operation="apply_enrollment" />
            <button class="form-button primary-action" type="button" :disabled="!canApplyEnrollment" @click="applyEnrollment">
              {{ t('admin.backups.actions.applyEnrollment') }}
            </button>
            <p v-if="error" class="error-text backup-enrollment-validation" role="alert">{{ error }}</p>
          </section>
        </div>
      </section>

      <section class="wire-section admin-panel backup-run-panel">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.run.title') }}</h2>
            <p>{{ t('admin.backups.run.subtitle') }}</p>
          </div>
          <button class="form-button primary-action" type="button" :disabled="!canSubmit || !connectionReady || !hasHostApproval" @click="runBackup">
            {{ inProgress ? t('admin.backups.actions.running') : t('admin.backups.actions.run') }}
          </button>
        </div>
        <HostCapabilityField v-if="connectionReady" v-model="hostApproval" operation="backup" />
        <div v-if="status.artifacts?.length" class="backup-artifact-list">
          <article v-for="artifact in status.artifacts" :key="artifact.remote_path" class="home-status-card refined-status-card backup-artifact-card">
            <span>{{ t(`admin.backups.artifacts.${artifact.artifact_type}`) }}</span>
            <strong>{{ artifact.filename }}</strong>
            <p>{{ formatBytes(artifact.size_bytes) }}</p>
            <dl class="system-update-meta backup-result-meta">
              <div><dt>{{ t('admin.backups.remotePath') }}</dt><dd>{{ artifact.remote_path }}</dd></div>
              <div><dt>{{ t('admin.backups.checksum') }}</dt><dd class="backup-checksum">{{ artifact.sha256 }}</dd></div>
            </dl>
          </article>
        </div>
        <p v-else class="muted">{{ t('admin.backups.noBackup') }}</p>
      </section>

      <p class="backup-host-log-note">{{ t('admin.backups.hostLogOnly') }}</p>
    </div>
  </StaffWorkspaceShell>
</template>
