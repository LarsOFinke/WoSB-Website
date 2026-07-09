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
  <nav class="navbar" :aria-label="t('common.mainNavigation')">
    <RouterLink class="nav-brand" to="/home">
      <span class="brand-mark" aria-hidden="true">IC</span>
      <span class="brand-copy">{{ t('common.projectName') }}</span>
    </RouterLink>

    <div class="nav-links" :aria-label="t('common.primaryNavigation')">
      <RouterLink class="nav-link" to="/home">{{ t('common.home') }}</RouterLink>
      <RouterLink class="nav-link" to="/builds">{{ t('common.builds') }}</RouterLink>
      <RouterLink class="nav-link" to="/groups">{{ t('common.groups') }}</RouterLink>
      <RouterLink class="nav-link" to="/forum">{{ t('common.forum') }}</RouterLink>
      <RouterLink class="nav-link" to="/calendar">{{ t('common.calendar') }}</RouterLink>
      <RouterLink class="nav-link" to="/fleets">{{ t('common.fleets') }}</RouterLink>
      <RouterLink class="nav-link" to="/guides">{{ t('common.guides') }}</RouterLink>
    </div>

    <div class="nav-account" :aria-label="t('common.accountNavigation')">
      <RouterLink v-if="isAuthenticated" class="nav-link nav-link-secondary" to="/profile">{{ t('common.profile') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="nav-link nav-link-secondary" to="/fleets/manage">{{ t('common.fleetManagement') }}</RouterLink>
      <RouterLink v-if="isStaff" class="nav-link nav-link-secondary" to="/admin">{{ t('common.staffPanel') }}</RouterLink>
    </div>

    <div class="nav-utilities">
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

      <div class="nav-session">
        <span v-if="isAuthenticated" class="session-user">{{ user.display_name }}</span>
        <button v-if="isAuthenticated" class="nav-action" type="button" @click="handleLogout">
          {{ t('auth.logout') }}
        </button>
        <template v-else>
          <RouterLink class="nav-action" to="/login">{{ t('auth.login') }}</RouterLink>
          <RouterLink class="nav-action nav-action-strong" to="/register">{{ t('auth.register') }}</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>
