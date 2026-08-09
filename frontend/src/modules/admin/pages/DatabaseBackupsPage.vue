<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useDatabaseBackupsPage } from '@/modules/admin/composables/useDatabaseBackupsPage'

const {
  t, isAdmin, user, navigationGroups, status, loading, error, success,
  inProgress, configured, connectionReady, canSubmit, stateLabel, operationLabel,
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

      <section class="wire-section admin-panel backup-run-panel">
        <div class="admin-panel-heading">
          <div>
            <h2>{{ t('admin.backups.run.title') }}</h2>
            <p>{{ t('admin.backups.run.subtitle') }}</p>
          </div>
          <button class="form-button primary-action" type="button" :disabled="!canSubmit || !connectionReady" @click="runBackup">
            {{ inProgress ? t('admin.backups.actions.running') : t('admin.backups.actions.run') }}
          </button>
        </div>
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
