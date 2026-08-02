<script setup>
import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import PrivacySelfService from '@/modules/accounts/components/PrivacySelfService.vue'
import { useSession } from '@/modules/accounts/session'
import { useCookieConsent } from '@/modules/privacy/composables/useCookieConsent'
import { usePrivacyCenterPage } from '@/modules/privacy/composables/usePrivacyCenterPage'
import '@/modules/privacy/styles/privacyCenter.css'

const { t } = useLocale()
const { user, isAuthenticated } = useSession()
const { openSettings } = useCookieConsent()
const workspace = usePrivacyCenterPage({ t })
</script>

<template>
  <div class="privacy-center page-stack">
    <PageHeader :eyebrow="t('privacy.center.eyebrow')" :title="t('privacy.center.title')" :description="t('privacy.center.description')" />

    <section class="wire-section privacy-center__grid" aria-labelledby="privacy-processing-title">
      <article>
        <h2 id="privacy-processing-title">{{ t('privacy.center.processingTitle') }}</h2>
        <p>{{ t('privacy.center.processingText') }}</p>
      </article>
      <article>
        <h2>{{ t('privacy.center.cookiesTitle') }}</h2>
        <p>{{ t('privacy.center.cookiesText') }}</p>
        <button class="form-button" type="button" @click="openSettings">{{ t('privacy.cookies.footerSettings') }}</button>
      </article>
      <article>
        <h2>{{ t('privacy.center.retentionTitle') }}</h2>
        <p>{{ t('privacy.center.retentionText') }}</p>
      </article>
      <article>
        <h2>{{ t('privacy.center.recipientsTitle') }}</h2>
        <p>{{ t('privacy.center.recipientsText') }}</p>
      </article>
    </section>

    <PrivacySelfService v-if="isAuthenticated && user" :username="user.username" />

    <section class="wire-section privacy-center__contact" aria-labelledby="privacy-contact-title">
      <div>
        <h2 id="privacy-contact-title">{{ t('privacy.center.contactTitle') }}</h2>
        <p>{{ t('privacy.center.contactText') }}</p>
      </div>
      <form @submit.prevent="workspace.submitContact">
        <label class="input-panel embedded-field"><span>{{ t('privacy.center.email') }}</span><input v-model="workspace.form.reply_email" type="email" maxlength="254" autocomplete="email" required /></label>
        <label class="input-panel embedded-field"><span>{{ t('privacy.center.subject') }}</span><input v-model="workspace.form.subject" maxlength="160" required /></label>
        <label class="input-panel embedded-field"><span>{{ t('privacy.center.message') }}</span><textarea v-model="workspace.form.message" maxlength="4000" rows="7" required></textarea></label>
        <label class="privacy-center__honeypot" aria-hidden="true">Website<input v-model="workspace.form.website" tabindex="-1" autocomplete="off" /></label>
        <button class="form-button primary-action" type="submit" :disabled="workspace.busy.value">{{ t('privacy.center.submit') }}</button>
        <p v-if="workspace.error.value" class="error-text" role="alert">{{ workspace.error.value }}</p>
        <p v-if="workspace.success.value" class="success-text" role="status">{{ workspace.success.value }}</p>
      </form>
    </section>
  </div>
</template>
