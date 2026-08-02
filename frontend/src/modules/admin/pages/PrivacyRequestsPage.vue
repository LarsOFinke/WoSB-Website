<script setup>
import { useLocale } from '@/locales'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { usePrivacyRequestsPage } from '@/modules/admin/composables/usePrivacyRequestsPage'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { user } = useSession()
const workspace = usePrivacyRequestsPage({ t })
</script>

<template>
  <StaffWorkspaceShell :eyebrow="t('common.staffPanel')" :title="t('privacy.data.adminTitle')" :description="t('privacy.data.adminDescription')" title-id="privacy-requests-title" :groups="createStaffNavigationGroups(t, { isAdmin: true })" active-key="privacy-requests" :user="user" :is-admin="true">
    <section class="wire-section admin-panel staff-management-panel">
      <p v-if="workspace.loading.value" class="muted table-state">{{ t('common.loading') }}</p>
      <p v-if="workspace.error.value" class="error-text table-state">{{ workspace.error.value }}</p>
      <p v-if="!workspace.loading.value && !workspace.requests.value.length" class="muted table-state">{{ t('privacy.data.empty') }}</p>
      <div class="admin-build-list">
        <article v-for="request in workspace.requests.value" :key="request.id" class="admin-build-row">
          <div class="admin-build-main">
            <strong>{{ request.subject_username }} · {{ t(`privacy.data.types.${request.request_type}`) }}</strong>
            <span>{{ t(`privacy.data.status.${request.status}`) }} · {{ request.created_at }}</span>
            <p>{{ request.details }}</p>
            <p v-if="request.resolution_note" class="muted">{{ request.resolution_note }}</p>
          </div>
          <div v-if="request.status === 'pending'" class="registration-actions">
            <label class="input-panel embedded-field"><span>{{ t('privacy.data.resolutionNote') }}</span><input v-model="workspace.notes[request.id]" maxlength="4000" required /></label>
            <div class="compact-actions">
              <button class="form-button primary-action" type="button" :disabled="workspace.busy.value === request.id" @click="workspace.resolve(request, 'complete')">{{ t('privacy.data.complete') }}</button>
              <button class="danger-action" type="button" :disabled="workspace.busy.value === request.id" @click="workspace.resolve(request, 'reject')">{{ t('privacy.data.reject') }}</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </StaffWorkspaceShell>
</template>
