<script setup>
import { computed } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import { createWorkspaceLinks } from '@/core/navigation/workspaceLinks'
import { useSession } from '@/modules/accounts/session'

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
const { canManageFleet, isAdmin, isAuthenticated, isStaff } = useSession()
const workspaceLinks = computed(() => createWorkspaceLinks(t, {
  isAuthenticated: isAuthenticated.value,
  isStaff: isStaff.value,
  isAdmin: isAdmin.value,
  canManageFleet: canManageFleet.value,
}))
const publicLinks = computed(() => workspaceLinks.value.filter((link) => link.section === 'public'))
const memberLinks = computed(() => workspaceLinks.value.filter((link) => link.section === 'member'))
const staffLinks = computed(() => workspaceLinks.value.filter((link) => link.section === 'staff'))
</script>

<template>
  <div class="sidebar-scrim" aria-hidden="true" @click="props.onCloseMobileMenu"></div>

  <aside
    id="workspace-sidebar"
    class="app-sidebar"
    :class="{ 'is-collapsed': props.isCollapsed, 'is-open': props.isOpen }"
    :aria-label="t('common.workspaceNavigation')"
  >
    <div class="sidebar-head">
      <div class="sidebar-title">
        <span>{{ t('common.workspace') }}</span>
        <strong>{{ t('common.commandDeck') }}</strong>
      </div>
      <button
        class="sidebar-collapse-button"
        type="button"
        :aria-label="props.isCollapsed ? t('common.expandMenu') : t('common.collapseMenu')"
        @click="props.onToggleSidebar"
      >
        <AppIcon :name="props.isCollapsed ? 'chevron-right' : 'chevron-left'" :size="18" />
      </button>
      <button class="sidebar-close-button" type="button" :aria-label="t('common.closeMenu')" @click="props.onCloseMobileMenu">
        <AppIcon name="close" :size="18" />
      </button>
    </div>

    <nav class="sidebar-nav" :aria-label="t('common.primaryNavigation')">
      <section class="sidebar-link-group">
        <span class="sidebar-section-label">{{ t('common.publicArea') }}</span>
        <RouterLink
          v-for="link in publicLinks"
          :key="link.to"
          class="sidebar-link"
          :to="link.to"
          :title="link.label"
          :exact="link.exact"
        >
          <span class="sidebar-link-icon" aria-hidden="true"><AppIcon :name="link.icon" :size="18" /></span>
          <span class="sidebar-link-label">{{ link.label }}</span>
        </RouterLink>
      </section>

      <section v-if="memberLinks.length" class="sidebar-link-group">
        <span class="sidebar-section-label">{{ t('common.memberArea') }}</span>
        <RouterLink v-for="link in memberLinks" :key="link.to" class="sidebar-link" :to="link.to" :title="link.label">
          <span class="sidebar-link-icon" aria-hidden="true"><AppIcon :name="link.icon" :size="18" /></span>
          <span class="sidebar-link-label">{{ link.label }}</span>
        </RouterLink>
      </section>

      <section v-if="staffLinks.length" class="sidebar-link-group">
        <span class="sidebar-section-label">{{ t('common.staffArea') }}</span>
        <RouterLink v-for="link in staffLinks" :key="link.to" class="sidebar-link is-staff-link" :to="link.to" :title="link.label">
          <span class="sidebar-link-icon" aria-hidden="true"><AppIcon :name="link.icon" :size="18" /></span>
          <span class="sidebar-link-label">{{ link.label }}</span>
        </RouterLink>
      </section>
    </nav>

    <div class="sidebar-access-card">
      <template v-if="isAuthenticated">
        <span>{{ t('common.personalArea') }}</span>
        <strong>{{ t('common.accountReady') }}</strong>
        <RouterLink class="sidebar-account-link" to="/profile">
          <AppIcon name="user" :size="16" />
          {{ t('common.profile') }}
          <AppIcon name="arrow-right" :size="15" />
        </RouterLink>
      </template>
      <template v-else>
        <span>{{ t('auth.loginEyebrow') }}</span>
        <strong>{{ t('auth.loginTitle') }}</strong>
        <RouterLink class="sidebar-account-link" to="/login">
          {{ t('auth.login') }}
          <AppIcon name="arrow-right" :size="15" />
        </RouterLink>
      </template>
    </div>
  </aside>
</template>
