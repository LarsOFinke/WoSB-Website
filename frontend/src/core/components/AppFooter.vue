<script setup>
import { useLocale } from '@/locales'

const { t } = useLocale()
</script>

<template>
  <footer class="wire-section footer">
    <span class="footer-text">{{ t('footer.text') }}</span>
  </footer>
</template>
