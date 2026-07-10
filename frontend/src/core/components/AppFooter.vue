<script setup>
import BrandLockup from '@/core/components/BrandLockup.vue'
import { useLocale } from '@/locales'

const { t } = useLocale()
</script>

<template>
  <footer class="wire-section footer">
    <BrandLockup compact />
    <span class="footer-text">{{ t('footer.tagline') }}</span>
    <span class="footer-meta">RBF · {{ new Date().getFullYear() }}</span>
  </footer>
</template>
