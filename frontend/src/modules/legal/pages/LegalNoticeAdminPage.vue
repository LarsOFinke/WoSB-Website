<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useLegalNoticeAdminPage } from '@/modules/legal/composables/useLegalNoticeAdminPage'
import '@/modules/legal/styles/legalNotice.css'

const {
  t, isAdmin, user, navigationGroups, form, meta, loading, saving, error, success,
  sourceLabel, updatedLabel, load, save, resetToEnvironment,
} = useLegalNoticeAdminPage()
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('legalNotice.admin.eyebrow')"
    :title="t('legalNotice.admin.title')"
    :description="t('legalNotice.admin.subtitle')"
    title-id="legal-notice-admin-title"
    :groups="navigationGroups"
    active-key="legal-notice"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions>
      <RouterLink class="button-box" to="/impressum">{{ t('legalNotice.admin.preview') }}</RouterLink>
      <RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink>
    </template>

    <section class="wire-section admin-panel legal-notice-admin-panel">
      <div class="admin-panel-heading">
        <div><h2>{{ t('legalNotice.admin.configurationTitle') }}</h2><p>{{ t('legalNotice.admin.configurationHint') }}</p></div>
        <span class="summary-pill">{{ sourceLabel }}</span>
      </div>

      <div class="legal-notice-legal-warning">
        <strong>{{ t('legalNotice.admin.legalWarningTitle') }}</strong>
        <p>{{ t('legalNotice.admin.legalWarningText') }}</p>
      </div>

      <p v-if="loading" class="muted table-state">{{ t('legalNotice.admin.loading') }}</p>
      <form v-else class="legal-notice-admin-form" @submit.prevent="save">
        <label class="legal-notice-publish-toggle">
          <input v-model="form.published" type="checkbox" />
          <span><strong>{{ t('legalNotice.admin.publish') }}</strong><small>{{ t('legalNotice.admin.publishHint') }}</small></span>
        </label>

        <fieldset>
          <legend>{{ t('legalNotice.sections.provider') }}</legend>
          <label><span>{{ t('legalNotice.fields.providerName') }} *</span><input v-model.trim="form.provider_name" maxlength="200" /></label>
          <label><span>{{ t('legalNotice.fields.legalForm') }}</span><input v-model.trim="form.legal_form" maxlength="120" /></label>
          <label class="is-wide"><span>{{ t('legalNotice.fields.representedBy') }}</span><input v-model.trim="form.represented_by" maxlength="300" /></label>
          <label class="is-wide"><span>{{ t('legalNotice.fields.street') }} *</span><input v-model.trim="form.street" maxlength="200" /></label>
          <label><span>{{ t('legalNotice.fields.postalCode') }} *</span><input v-model.trim="form.postal_code" maxlength="32" /></label>
          <label><span>{{ t('legalNotice.fields.city') }} *</span><input v-model.trim="form.city" maxlength="120" /></label>
          <label><span>{{ t('legalNotice.fields.country') }} *</span><input v-model.trim="form.country" maxlength="120" /></label>
        </fieldset>

        <fieldset>
          <legend>{{ t('legalNotice.sections.contact') }}</legend>
          <label><span>{{ t('legalNotice.fields.email') }} *</span><input v-model.trim="form.email" type="email" maxlength="254" /></label>
          <label><span>{{ t('legalNotice.fields.phone') }}</span><input v-model.trim="form.phone" type="tel" maxlength="80" /></label>
        </fieldset>

        <fieldset>
          <legend>{{ t('legalNotice.sections.register') }}</legend>
          <label><span>{{ t('legalNotice.fields.registerName') }}</span><input v-model.trim="form.register_name" maxlength="160" /></label>
          <label><span>{{ t('legalNotice.fields.registerCourt') }}</span><input v-model.trim="form.register_court" maxlength="200" /></label>
          <label><span>{{ t('legalNotice.fields.registerNumber') }}</span><input v-model.trim="form.register_number" maxlength="120" /></label>
          <label><span>{{ t('legalNotice.fields.vatId') }}</span><input v-model.trim="form.vat_id" maxlength="80" /></label>
          <label><span>{{ t('legalNotice.fields.businessId') }}</span><input v-model.trim="form.business_id" maxlength="120" /></label>
          <label class="is-wide"><span>{{ t('legalNotice.fields.supervisoryAuthority') }}</span><textarea v-model.trim="form.supervisory_authority" rows="3" maxlength="500"></textarea></label>
        </fieldset>

        <fieldset>
          <legend>{{ t('legalNotice.sections.editorial') }}</legend>
          <p class="legal-notice-fieldset-hint">{{ t('legalNotice.admin.editorialHint') }}</p>
          <label><span>{{ t('legalNotice.fields.editorialName') }}</span><input v-model.trim="form.editorial_responsible_name" maxlength="200" /></label>
          <label class="is-wide"><span>{{ t('legalNotice.fields.street') }}</span><input v-model.trim="form.editorial_responsible_street" maxlength="200" /></label>
          <label><span>{{ t('legalNotice.fields.postalCode') }}</span><input v-model.trim="form.editorial_responsible_postal_code" maxlength="32" /></label>
          <label><span>{{ t('legalNotice.fields.city') }}</span><input v-model.trim="form.editorial_responsible_city" maxlength="120" /></label>
          <label><span>{{ t('legalNotice.fields.country') }}</span><input v-model.trim="form.editorial_responsible_country" maxlength="120" /></label>
        </fieldset>

        <fieldset>
          <legend>{{ t('legalNotice.sections.transparency') }}</legend>
          <p class="legal-notice-fieldset-hint">{{ t('legalNotice.admin.repositoryHint') }}</p>
          <label class="is-wide">
            <span>{{ t('legalNotice.fields.publicRepositoryUrl') }}</span>
            <input
              v-model.trim="form.public_repository_url"
              type="url"
              inputmode="url"
              maxlength="2048"
              pattern="https://(?![^/]*@).*"
              placeholder="https://github.com/organization/project"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>{{ t('legalNotice.sections.additional') }}</legend>
          <label class="is-wide"><span>{{ t('legalNotice.fields.disputeResolution') }}</span><textarea v-model.trim="form.dispute_resolution_text" rows="5" maxlength="4000"></textarea><small>{{ t('legalNotice.admin.disputeHint') }}</small></label>
          <label class="is-wide"><span>{{ t('legalNotice.fields.additionalInformation') }}</span><textarea v-model.trim="form.additional_information" rows="5" maxlength="4000"></textarea></label>
        </fieldset>

        <p v-if="updatedLabel" class="muted legal-notice-admin-meta">{{ t('legalNotice.admin.updatedBy', { user: meta.updated_by_username, date: updatedLabel }) }}</p>
        <p v-if="error" class="error-text table-state" role="alert">{{ error }}</p>
        <p v-if="success" class="success-text table-state" role="status">{{ success }}</p>

        <div class="legal-notice-admin-actions">
          <button class="form-button primary-action" type="submit" :disabled="saving">{{ saving ? t('legalNotice.admin.saving') : t('legalNotice.admin.save') }}</button>
          <button class="small-action" type="button" :disabled="saving" @click="load">{{ t('legalNotice.admin.reload') }}</button>
          <button class="danger-action" type="button" :disabled="saving" @click.prevent="resetToEnvironment">{{ t('legalNotice.admin.resetEnvironment') }}</button>
        </div>
      </form>
    </section>
  </StaffWorkspaceShell>
</template>
