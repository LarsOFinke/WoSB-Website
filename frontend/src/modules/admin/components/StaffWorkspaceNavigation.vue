<script setup>
import { computed, ref } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import StaffNavigationMenu from '@/modules/admin/components/StaffNavigationMenu.vue'
import { staffNavigationLabel } from '@/modules/admin/domain/staffNavigation'
import { useLocale } from '@/locales'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  isAdmin: { type: Boolean, default: false },
})

const { t } = useLocale()
const mobileOpen = ref(false)
const activeLabel = computed(() => staffNavigationLabel(props.groups, props.activeKey))

function closeMobileNavigation() {
  mobileOpen.value = false
}
</script>

<template>
  <div class="staff-navigation">
    <button
      class="staff-navigation-trigger"
      type="button"
      :aria-expanded="mobileOpen"
      aria-controls="staff-navigation-mobile-panel"
      @click="mobileOpen = true"
    >
      <span class="staff-navigation-trigger-icon"><AppIcon name="compass" :size="20" /></span>
      <span><small>{{ t('admin.tabsLabel') }}</small><strong>{{ activeLabel }}</strong></span>
      <AppIcon name="menu" :size="21" />
    </button>

    <aside class="staff-navigation-desktop">
      <StaffNavigationMenu :groups="groups" :active-key="activeKey" />
      <div class="staff-navigation-scope" :class="{ 'is-admin': isAdmin }">
        <AppIcon :name="isAdmin ? 'shield' : 'lock'" :size="18" />
        <div>
          <strong>{{ isAdmin ? t('admin.workspace.adminScopeTitle') : t('admin.workspace.moderatorScopeTitle') }}</strong>
          <span>{{ isAdmin ? t('roles.admin') : t('roles.moderator') }}</span>
        </div>
      </div>
    </aside>

    <Teleport to="body">
      <div v-if="mobileOpen" class="staff-navigation-mobile-layer" @click.self="closeMobileNavigation">
        <aside id="staff-navigation-mobile-panel" class="staff-navigation-mobile-panel" role="dialog" aria-modal="true" :aria-label="t('admin.tabsLabel')">
          <header>
            <div><small>{{ t('admin.tabsLabel') }}</small><strong>{{ activeLabel }}</strong></div>
            <button class="small-action" type="button" @click="closeMobileNavigation"><AppIcon name="close" :size="18" /><span class="sr-only">{{ t('common.close') }}</span></button>
          </header>
          <StaffNavigationMenu :groups="groups" :active-key="activeKey" @navigate="closeMobileNavigation" />
          <div class="staff-navigation-scope" :class="{ 'is-admin': isAdmin }">
            <AppIcon :name="isAdmin ? 'shield' : 'lock'" :size="18" />
            <div><strong>{{ isAdmin ? t('admin.workspace.adminScopeTitle') : t('admin.workspace.moderatorScopeTitle') }}</strong><span>{{ isAdmin ? t('roles.admin') : t('roles.moderator') }}</span></div>
          </div>
        </aside>
      </div>
    </Teleport>
  </div>
</template>
