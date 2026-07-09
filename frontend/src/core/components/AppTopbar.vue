<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/services/session'

const props = defineProps({
  onOpenMobileMenu: {
    type: Function,
    required: true,
  },
})

const router = useRouter()
const { locale, setLocale, supportedLocales, t } = useLocale()
const { isAuthenticated, isStaff, loadSession, logout, sessionState, user } = useSession()

const profileLinkLabel = computed(() => {
  const displayName = user.value?.display_name || user.value?.username
  return displayName ? `${t('common.profile')} · ${displayName}` : t('common.profile')
})

async function handleLogout() {
  await logout()
  if (router.currentRoute.value.meta.requiresStaff || router.currentRoute.value.meta.requiresUser) {
    router.push('/')
  }
}

onMounted(() => {
  if (!sessionState.isReady) {
    loadSession()
  }
})
</script>

<template>
  <header class="app-topbar" :aria-label="t('common.mainNavigation')">
    <div class="topbar-brand-group">
      <button class="mobile-menu-button" type="button" :aria-label="t('common.openMenu')" @click="props.onOpenMobileMenu">
        <span aria-hidden="true">☰</span>
      </button>

      <RouterLink class="topbar-brand" to="/">
        <span class="brand-mark" aria-hidden="true">IC</span>
        <span class="brand-copy">{{ t('common.projectName') }}</span>
      </RouterLink>
    </div>

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

    <nav class="topbar-primary" :aria-label="t('common.accountNavigation')">
      <span v-if="isAuthenticated" class="topbar-section-label">{{ t('common.personalArea') }}</span>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/profile">{{ profileLinkLabel }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/profile/builds">{{ t('common.myBuilds') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/profile/groups">{{ t('common.myGroupSearches') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/fleets">{{ t('common.fleetManagement') }}</RouterLink>
      <RouterLink v-if="isStaff" class="topbar-link topbar-link-strong" to="/admin">{{ t('common.staffPanel') }}</RouterLink>
    </nav>

    <div class="topbar-actions">
      <div class="topbar-session">
        <button v-if="isAuthenticated" class="topbar-action" type="button" @click="handleLogout">
          {{ t('auth.logout') }}
        </button>
        <template v-else>
          <RouterLink class="topbar-action" to="/login">{{ t('auth.login') }}</RouterLink>
          <RouterLink class="topbar-action topbar-action-strong" to="/register">{{ t('auth.register') }}</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
