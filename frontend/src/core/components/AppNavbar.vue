<script setup>
import AppSidebar from '@/core/components/AppSidebar.vue'
import AppTopbar from '@/core/components/AppTopbar.vue'
import { useAppShell } from '@/core/composables/useAppShell'

const {
  closeMobileMenu,
  isMobileMenuOpen,
  isSidebarCollapsed,
  openMobileMenu,
  toggleSidebar,
} = useAppShell()
</script>

<template>
  <AppTopbar :on-open-mobile-menu="openMobileMenu" />
  <AppSidebar
    :is-collapsed="isSidebarCollapsed"
    :is-open="isMobileMenuOpen"
    :on-close-mobile-menu="closeMobileMenu"
    :on-toggle-sidebar="toggleSidebar"
  />
</template>
