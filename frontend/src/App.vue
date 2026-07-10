<script setup>
import AppFooter from '@/core/components/AppFooter.vue'
import AppNavbar from '@/core/components/AppNavbar.vue'
import { useLocale } from '@/locales'

const { t } = useLocale()
</script>

<template>
  <a class="skip-link" href="#main-content">{{ t('common.skipToContent') }}</a>
  <div class="app-shell">
    <AppNavbar />
    <main id="main-content" class="app-main" tabindex="-1">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>
