<template>
  <div class="app-shell">
    <AppHeader />

    <main class="page-container">
      <RouterView />
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import AppFooter from '@/components/layout/AppFooter.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
</script>
