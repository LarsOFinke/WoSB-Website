<script setup>
import { useLegalNoticePage } from '@/modules/legal/composables/useLegalNoticePage'
import '@/modules/legal/styles/legalNotice.css'

const {
  t, notice, loading, error, providerAddress, editorialAddress, registerDetails,
  hasRegisterDetails, hasTaxDetails, hasEditorialResponsibility, publicRepositoryUrl,
  lastUpdated, loadNotice,
} = useLegalNoticePage()
</script>

<template>
  <section class="legal-notice-page page-frame" aria-labelledby="legal-notice-title">
    <header class="legal-notice-hero wire-frame">
      <p class="eyebrow">{{ t('legalNotice.public.eyebrow') }}</p>
      <h1 id="legal-notice-title">{{ t('legalNotice.public.title') }}</h1>
      <p>{{ t('legalNotice.public.subtitle') }}</p>
    </header>

    <section v-if="loading" class="wire-section legal-notice-state" aria-live="polite">
      <p>{{ t('legalNotice.public.loading') }}</p>
    </section>

    <section v-else-if="error" class="wire-section legal-notice-state" role="alert">
      <p class="error-text">{{ error }}</p>
      <button class="small-action" type="button" @click="loadNotice">{{ t('legalNotice.public.retry') }}</button>
    </section>

    <section v-else-if="!notice.published" class="wire-section legal-notice-state legal-notice-draft">
      <h2>{{ t('legalNotice.public.draftTitle') }}</h2>
      <p>{{ t('legalNotice.public.draftText') }}</p>
      <small>{{ t('legalNotice.public.draftLegalHint') }}</small>
    </section>

    <div v-else class="legal-notice-grid">
      <section class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.provider') }}</h2>
        <address>
          <strong>{{ notice.provider_name }}</strong>
          <span v-if="notice.legal_form">{{ notice.legal_form }}</span>
          <span v-if="notice.represented_by">{{ t('legalNotice.fields.representedBy') }}: {{ notice.represented_by }}</span>
          <span v-for="line in providerAddress" :key="line">{{ line }}</span>
        </address>
      </section>

      <section class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.contact') }}</h2>
        <dl>
          <div><dt>{{ t('legalNotice.fields.email') }}</dt><dd><a :href="`mailto:${notice.email}`">{{ notice.email }}</a></dd></div>
          <div v-if="notice.phone"><dt>{{ t('legalNotice.fields.phone') }}</dt><dd><a :href="`tel:${notice.phone}`">{{ notice.phone }}</a></dd></div>
        </dl>
      </section>

      <section v-if="hasRegisterDetails" class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.register') }}</h2>
        <dl>
          <div v-if="notice.register_name"><dt>{{ t('legalNotice.fields.registerName') }}</dt><dd>{{ notice.register_name }}</dd></div>
          <div v-if="notice.register_court"><dt>{{ t('legalNotice.fields.registerCourt') }}</dt><dd>{{ notice.register_court }}</dd></div>
          <div v-if="notice.register_number"><dt>{{ t('legalNotice.fields.registerNumber') }}</dt><dd>{{ notice.register_number }}</dd></div>
        </dl>
      </section>

      <section v-if="hasTaxDetails" class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.tax') }}</h2>
        <dl>
          <div v-if="notice.vat_id"><dt>{{ t('legalNotice.fields.vatId') }}</dt><dd>{{ notice.vat_id }}</dd></div>
          <div v-if="notice.business_id"><dt>{{ t('legalNotice.fields.businessId') }}</dt><dd>{{ notice.business_id }}</dd></div>
        </dl>
      </section>

      <section v-if="notice.supervisory_authority" class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.supervision') }}</h2>
        <p class="legal-notice-preline">{{ notice.supervisory_authority }}</p>
      </section>

      <section v-if="hasEditorialResponsibility" class="wire-section legal-notice-card">
        <h2>{{ t('legalNotice.sections.editorial') }}</h2>
        <address>
          <strong>{{ notice.editorial_responsible_name }}</strong>
          <span v-for="line in editorialAddress" :key="line">{{ line }}</span>
        </address>
      </section>

      <section v-if="publicRepositoryUrl" class="wire-section legal-notice-card legal-notice-repository legal-notice-wide">
        <div>
          <p class="eyebrow">{{ t('legalNotice.sections.transparency') }}</p>
          <h2>{{ t('legalNotice.public.repositoryTitle') }}</h2>
          <p>{{ t('legalNotice.public.repositoryText') }}</p>
        </div>
        <a class="button-box" :href="publicRepositoryUrl" target="_blank" rel="noopener noreferrer">
          {{ t('legalNotice.public.repositoryLink') }}
          <span aria-hidden="true">↗</span>
        </a>
      </section>

      <section v-if="notice.dispute_resolution_text" class="wire-section legal-notice-card legal-notice-wide">
        <h2>{{ t('legalNotice.sections.dispute') }}</h2>
        <p class="legal-notice-preline">{{ notice.dispute_resolution_text }}</p>
      </section>

      <section v-if="notice.additional_information" class="wire-section legal-notice-card legal-notice-wide">
        <h2>{{ t('legalNotice.sections.additional') }}</h2>
        <p class="legal-notice-preline">{{ notice.additional_information }}</p>
      </section>

      <p v-if="lastUpdated" class="legal-notice-updated legal-notice-wide">
        {{ t('legalNotice.public.updated', { date: lastUpdated }) }}
      </p>
    </div>
  </section>
</template>
