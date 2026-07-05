<script setup>
import AppFooter from '@/core/components/AppFooter.vue'
import AppNavbar from '@/core/components/AppNavbar.vue'
</script>

<template>
  <div class="app-shell">
    <AppNavbar />
    <main class="app-main">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>
