<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { createWorkspaceLinks } from '@/core/navigation/workspaceLinks'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    required: true,
  },
  isOpen: {
    type: Boolean,
    required: true,
  },
  onCloseMobileMenu: {
    type: Function,
    required: true,
  },
  onToggleSidebar: {
    type: Function,
    required: true,
  },
})

const { t } = useLocale()
const workspaceLinks = computed(() => createWorkspaceLinks(t))
</script>

<template>
  <div class="sidebar-scrim" aria-hidden="true" @click="props.onCloseMobileMenu"></div>

  <aside
    class="app-sidebar"
    :class="{ 'is-collapsed': props.isCollapsed, 'is-open': props.isOpen }"
    :aria-label="t('common.workspaceNavigation')"
  >
    <div class="sidebar-head">
      <div class="sidebar-title">
        <span>{{ t('common.workspace') }}</span>
        <strong>{{ t('common.modules') }}</strong>
      </div>
      <button
        class="sidebar-collapse-button"
        type="button"
        :aria-label="props.isCollapsed ? t('common.expandMenu') : t('common.collapseMenu')"
        @click="props.onToggleSidebar"
      >
        <span aria-hidden="true">{{ props.isCollapsed ? '→' : '←' }}</span>
      </button>
      <button class="sidebar-close-button" type="button" :aria-label="t('common.closeMenu')" @click="props.onCloseMobileMenu">
        <span aria-hidden="true">×</span>
      </button>
    </div>

    <nav class="sidebar-nav" :aria-label="t('common.primaryNavigation')">
      <RouterLink
        v-for="link in workspaceLinks"
        :key="link.to"
        class="sidebar-link"
        :to="link.to"
        :title="link.label"
        :exact="link.exact"
      >
        <span class="sidebar-link-icon" aria-hidden="true">{{ link.icon }}</span>
        <span class="sidebar-link-label">{{ link.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
