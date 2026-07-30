<script setup>
import BrandLockup from '@/core/components/BrandLockup.vue'
import { useLocale } from '@/locales'
import { useCookieConsent } from '@/modules/privacy/composables/useCookieConsent'

const { t } = useLocale()
const { openSettings } = useCookieConsent()
</script>

<template>
  <footer class="wire-section footer">
    <BrandLockup compact />
    <span class="footer-text">{{ t('footer.tagline') }}</span>
    <RouterLink class="footer-legal-link" to="/impressum">{{ t('legalNotice.public.footerLink') }}</RouterLink>
    <button type="button" class="footer-cookie-settings" @click="openSettings">{{ t('privacy.cookies.footerSettings') }}</button>
    <span class="footer-meta">RBF · {{ new Date().getFullYear() }}</span>
  </footer>
</template>
