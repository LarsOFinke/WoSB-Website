<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const props = defineProps({
  onOpenMobileMenu: {
    type: Function,
    required: true,
  },
})

const router = useRouter()
const { locale, setLocale, supportedLocales, t } = useLocale()
const { isAuthenticated, isStaff, loadSession, logout, sessionState, user } = useSession()

const profileLinkLabel = computed(() => user.value?.display_name || user.value?.username || t('common.profile'))
const userInitials = computed(() => {
  const source = profileLinkLabel.value.trim().split(/\s+/).filter(Boolean)
  return source.slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'BM'
})

async function handleLogout() {
  await logout()
  if (router.currentRoute.value.meta.requiresStaff || router.currentRoute.value.meta.requiresUser) {
    router.push('/')
  }
}

onMounted(() => {
  if (!sessionState.isReady) loadSession()
})
</script>

<template>
  <header class="app-topbar" :aria-label="t('common.mainNavigation')">
    <div class="topbar-brand-group">
      <button class="mobile-menu-button" type="button" :aria-label="t('common.openMenu')" @click="props.onOpenMobileMenu">
        <span aria-hidden="true">☰</span>
      </button>

      <RouterLink class="topbar-brand" to="/">
        <span class="brand-mark" aria-hidden="true">BM</span>
        <span class="brand-copy">
          <strong>{{ t('common.projectName') }}</strong>
          <small>{{ t('fleets.singleBadge') }}</small>
        </span>
      </RouterLink>
    </div>

    <nav class="topbar-primary" :aria-label="t('common.primaryNavigation')">
      <RouterLink class="topbar-link" to="/">{{ t('common.home') }}</RouterLink>
      <RouterLink class="topbar-link" to="/builds">{{ t('common.builds') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/guides">{{ t('common.guides') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/groups">{{ t('common.groups') }}</RouterLink>
      <RouterLink v-if="isStaff" class="topbar-link topbar-link-strong" to="/admin">{{ t('common.staffPanel') }}</RouterLink>
    </nav>

    <div class="topbar-actions">
      <div class="locale-switcher topbar-locale" :aria-label="t('common.language')">
        <button
          v-for="entry in supportedLocales"
          :key="entry.code"
          class="locale-button"
          :class="{ 'is-active': locale === entry.code }"
          type="button"
          @click="setLocale(entry.code)"
        >
          {{ entry.label }}
        </button>
      </div>

      <div class="topbar-session">
        <template v-if="isAuthenticated">
          <RouterLink class="topbar-account-summary" to="/profile">
            <span class="account-avatar" aria-hidden="true">{{ userInitials }}</span>
            <span class="account-copy">
              <strong>{{ profileLinkLabel }}</strong>
              <small>{{ t(`roles.${user?.role || 'user'}`) }}</small>
            </span>
          </RouterLink>
          <button class="topbar-action" type="button" @click="handleLogout">{{ t('auth.logout') }}</button>
        </template>
        <template v-else>
          <RouterLink class="topbar-action" to="/login">{{ t('auth.login') }}</RouterLink>
          <RouterLink class="topbar-action topbar-action-strong" to="/register">{{ t('auth.register') }}</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
