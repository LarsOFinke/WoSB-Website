<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/services/session'

const SIDEBAR_STORAGE_KEY = 'wosb.sidebar.collapsed'

const router = useRouter()
const route = useRoute()
const { locale, setLocale, supportedLocales, t } = useLocale()
const { isAuthenticated, isStaff, loadSession, logout, sessionState, user } = useSession()

const isSidebarCollapsed = ref(false)
const isMobileMenuOpen = ref(false)

const workspaceLinks = computed(() => [
  { to: '/home', label: t('common.home'), icon: '⌂', exact: true },
  { to: '/builds', label: t('common.builds'), icon: '⚙' },
  { to: '/groups', label: t('common.groups'), icon: '◈' },
  { to: '/forum', label: t('common.forum'), icon: '✦' },
  { to: '/calendar', label: t('common.calendar'), icon: '□' },
  { to: '/fleets', label: t('common.fleets'), icon: '△' },
  { to: '/guides', label: t('common.guides'), icon: '☰' },
])

const personalLinks = computed(() => {
  if (!isAuthenticated.value) return []
  return [
    { to: '/profile/builds', label: t('common.myBuilds'), icon: '◇' },
    { to: '/profile/groups', label: t('common.myAnnouncements'), icon: '◌' },
  ]
})

function syncShellClass() {
  if (typeof document === 'undefined') return
  document.body.classList.toggle('sidebar-collapsed', isSidebarCollapsed.value)
  document.body.classList.toggle('mobile-sidebar-open', isMobileMenuOpen.value)
}

function readSidebarPreference() {
  if (typeof localStorage === 'undefined') return false
  return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true'
}

function persistSidebarPreference() {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(isSidebarCollapsed.value))
  }
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  persistSidebarPreference()
  syncShellClass()
}

function openMobileMenu() {
  isMobileMenuOpen.value = true
  syncShellClass()
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
  syncShellClass()
}

async function handleLogout() {
  await logout()
  closeMobileMenu()
  if (router.currentRoute.value.meta.requiresStaff || router.currentRoute.value.meta.requiresUser) {
    router.push('/home')
  }
}

watch(() => route.fullPath, () => {
  closeMobileMenu()
})

onMounted(() => {
  isSidebarCollapsed.value = readSidebarPreference()
  syncShellClass()
  if (!sessionState.isReady) {
    loadSession()
  }
})
</script>

<template>
  <header class="app-topbar" :aria-label="t('common.mainNavigation')">
    <div class="topbar-brand-group">
      <button class="mobile-menu-button" type="button" :aria-label="t('common.openMenu')" @click="openMobileMenu">
        <span aria-hidden="true">☰</span>
      </button>

      <RouterLink class="topbar-brand" to="/home">
        <span class="brand-mark" aria-hidden="true">IC</span>
        <span class="brand-copy">{{ t('common.projectName') }}</span>
      </RouterLink>
    </div>

    <nav class="topbar-primary" :aria-label="t('common.accountNavigation')">
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/profile">{{ t('common.profile') }}</RouterLink>
      <RouterLink v-if="isAuthenticated" class="topbar-link" to="/fleets/manage">{{ t('common.fleetManagement') }}</RouterLink>
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
        <span v-if="isAuthenticated" class="session-user">{{ user.display_name }}</span>
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

  <div class="sidebar-scrim" aria-hidden="true" @click="closeMobileMenu"></div>

  <aside
    class="app-sidebar"
    :class="{ 'is-collapsed': isSidebarCollapsed, 'is-open': isMobileMenuOpen }"
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
        :aria-label="isSidebarCollapsed ? t('common.expandMenu') : t('common.collapseMenu')"
        @click="toggleSidebar"
      >
        <span aria-hidden="true">{{ isSidebarCollapsed ? '→' : '←' }}</span>
      </button>
      <button class="sidebar-close-button" type="button" :aria-label="t('common.closeMenu')" @click="closeMobileMenu">
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

    <div v-if="personalLinks.length" class="sidebar-section">
      <span class="sidebar-section-label">{{ t('common.personalArea') }}</span>
      <nav class="sidebar-nav sidebar-nav-compact" :aria-label="t('common.personalArea')">
        <RouterLink v-for="link in personalLinks" :key="link.to" class="sidebar-link" :to="link.to" :title="link.label">
          <span class="sidebar-link-icon" aria-hidden="true">{{ link.icon }}</span>
          <span class="sidebar-link-label">{{ link.label }}</span>
        </RouterLink>
      </nav>
    </div>
  </aside>
</template>
