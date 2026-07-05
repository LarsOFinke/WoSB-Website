<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/services/session'

const router = useRouter()
const { locale, setLocale, supportedLocales, t } = useLocale()
const { isAuthenticated, isStaff, loadSession, logout, sessionState, user } = useSession()

async function handleLogout() {
  await logout()
  if (router.currentRoute.value.meta.requiresStaff || router.currentRoute.value.meta.requiresUser) {
    router.push('/home')
  }
}

onMounted(() => {
  if (!sessionState.isReady) {
    loadSession()
  }
})
</script>

<template>
  <nav class="wire-section navbar" :aria-label="t('common.mainNavigation')">
    <RouterLink class="nav-brand" to="/home">{{ t('common.projectName') }}</RouterLink>

    <div class="nav-links">
      <RouterLink class="nav-link" to="/home">{{ t('common.home') }}</RouterLink>
      <RouterLink class="nav-link" to="/builds">{{ t('common.builds') }}</RouterLink>
      <RouterLink class="nav-link" to="/groups">{{ t('common.groups') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="nav-link" to="/profile">{{ t('common.profile') }}</RouterLink>
      <RouterLink v-if="isStaff" class="nav-link" to="/admin">{{ t('common.staffPanel') }}</RouterLink>
    </div>

    <div class="nav-session">
      <span v-if="isAuthenticated" class="session-user">{{ user.display_name }}</span>
      <button v-if="isAuthenticated" class="nav-action" type="button" @click="handleLogout">
        {{ t('auth.logout') }}
      </button>
      <template v-else>
        <RouterLink class="nav-action" to="/login">{{ t('auth.login') }}</RouterLink>
        <RouterLink class="nav-action" to="/register">{{ t('auth.register') }}</RouterLink>
      </template>
    </div>

    <div class="locale-switcher" :aria-label="t('common.language')">
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
  </nav>
</template>
