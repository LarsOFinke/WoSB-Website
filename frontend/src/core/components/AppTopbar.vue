<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/core/components/AppIcon.vue'
import BrandLockup from '@/core/components/BrandLockup.vue'
import { createPersonalLinks } from '@/core/navigation/workspaceLinks'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const props = defineProps({
  isMobileMenuOpen: {
    type: Boolean,
    required: true,
  },
  onOpenMobileMenu: {
    type: Function,
    required: true,
  },
})

const router = useRouter()
const { locale, localeLoading, setLocale, supportedLocales, t } = useLocale()
const { canAuthorContent, isAuthenticated, loadSession, logout, sessionState, user } = useSession()

const profileLinkLabel = computed(() => user.value?.display_name || user.value?.username || t('common.profile'))
const userInitials = computed(() => {
  const source = profileLinkLabel.value.trim().split(/\s+/).filter(Boolean)
  return source.slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'RBF'
})
const primaryLinks = computed(() => createPersonalLinks(t, {
  isAuthenticated: isAuthenticated.value,
  canAuthorContent: canAuthorContent.value,
}))

async function handleLogout() {
  await logout()
  if (router.currentRoute.value.meta.requiresStaff || router.currentRoute.value.meta.requiresUser
    || router.currentRoute.value.meta.requiresContentAuthor) {
    router.push('/')
  }
}

async function handleLocaleChange(event) {
  const selectedLocale = event.target.value
  if (!await setLocale(selectedLocale)) event.target.value = locale.value
}

onMounted(() => {
  if (!sessionState.isReady) loadSession()
})
</script>

<template>
  <header class="app-topbar" :aria-label="t('common.mainNavigation')">
    <div class="topbar-brand-group">
      <button class="mobile-menu-button" type="button" :aria-label="t('common.openMenu')" aria-controls="workspace-sidebar" :aria-expanded="props.isMobileMenuOpen" @click="props.onOpenMobileMenu">
        <AppIcon name="menu" />
      </button>

      <RouterLink class="topbar-brand" to="/" :aria-label="t('common.projectName')">
        <BrandLockup />
      </RouterLink>
    </div>

    <nav class="topbar-primary" :aria-label="t('common.primaryNavigation')">
      <RouterLink
        v-for="link in primaryLinks"
        :key="link.to"
        class="topbar-link"
        :to="link.to"
        :title="link.label"
      >
        <AppIcon :name="link.icon" :size="17" />
        <span>{{ link.label }}</span>
      </RouterLink>
    </nav>

    <div class="topbar-actions">
      <label class="topbar-locale-select">
        <AppIcon name="globe" :size="17" />
        <span class="sr-only">{{ t('common.language') }}</span>
        <select :value="locale" :aria-label="t('common.language')" :disabled="Boolean(localeLoading)" @change="handleLocaleChange">
          <option v-for="entry in supportedLocales" :key="entry.code" :value="entry.code">{{ entry.label }}</option>
        </select>
      </label>

      <div class="topbar-session">
        <template v-if="isAuthenticated">
          <RouterLink class="topbar-account-summary" to="/profile">
            <span class="account-avatar" aria-hidden="true">{{ userInitials }}</span>
            <span class="account-copy">
              <strong>{{ profileLinkLabel }}</strong>
              <small>{{ t(`roles.${user?.role || 'user'}`) }}</small>
            </span>
          </RouterLink>
          <button class="topbar-action topbar-icon-action" type="button" :aria-label="t('auth.logout')" :title="t('auth.logout')" @click="handleLogout">
            <AppIcon name="logout" :size="17" />
          </button>
        </template>
        <template v-else>
          <RouterLink class="topbar-action" to="/login">
            <AppIcon name="login" :size="17" />
            <span>{{ t('auth.login') }}</span>
          </RouterLink>
          <RouterLink class="topbar-action topbar-action-strong" to="/register">{{ t('auth.register') }}</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
