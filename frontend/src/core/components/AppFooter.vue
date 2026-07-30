<script setup>
import BrandLockup from '@/core/components/BrandLockup.vue'
import { useLocale } from '@/locales'
import { useCookieConsent } from '@/modules/privacy/composables/useCookieConsent'

const { t } = useLocale()
const { openSettings } = useCookieConsent()
</script>

<template>
  <footer class="wire-section app-footer">
    <div class="app-footer-identity">
      <BrandLockup compact />
      <span class="app-footer-tagline">{{ t('footer.tagline') }}</span>
    </div>

    <nav class="app-footer-actions" :aria-label="t('footer.tagline')">
      <RouterLink class="app-footer-link" to="/impressum">
        {{ t('legalNotice.public.footerLink') }}
      </RouterLink>
      <button type="button" class="app-footer-link app-footer-button" @click="openSettings">
        {{ t('privacy.cookies.footerSettings') }}
      </button>
    </nav>

    <span class="app-footer-meta">RBF · {{ new Date().getFullYear() }}</span>
  </footer>
</template>
