import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const SIDEBAR_STORAGE_KEY = 'rbf-hub.sidebar.collapsed'
const LEGACY_SIDEBAR_STORAGE_KEYS = ['rbv-hub.sidebar.collapsed', 'blackwater-hub.sidebar.collapsed']

function syncShellClass(isSidebarCollapsed, isMobileMenuOpen) {
  if (typeof document === 'undefined') return
  document.body.classList.toggle('sidebar-collapsed', isSidebarCollapsed.value)
  document.body.classList.toggle('mobile-sidebar-open', isMobileMenuOpen.value)
}

function readSidebarPreference() {
  if (typeof localStorage === 'undefined') return false
  const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY) ?? LEGACY_SIDEBAR_STORAGE_KEYS.map((key) => localStorage.getItem(key)).find((value) => value !== null)
  if (stored !== null && localStorage.getItem(SIDEBAR_STORAGE_KEY) === null) localStorage.setItem(SIDEBAR_STORAGE_KEY, stored)
  return stored === 'true'
}

function persistSidebarPreference(value) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(value))
  }
}

export function useAppShell() {
  const route = useRoute()
  const isSidebarCollapsed = ref(false)
  const isMobileMenuOpen = ref(false)

  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
    persistSidebarPreference(isSidebarCollapsed.value)
    syncShellClass(isSidebarCollapsed, isMobileMenuOpen)
  }

  function openMobileMenu() {
    isMobileMenuOpen.value = true
    syncShellClass(isSidebarCollapsed, isMobileMenuOpen)
  }

  function closeMobileMenu() {
    isMobileMenuOpen.value = false
    syncShellClass(isSidebarCollapsed, isMobileMenuOpen)
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && isMobileMenuOpen.value) closeMobileMenu()
  }

  watch(() => route.fullPath, closeMobileMenu)

  onMounted(() => {
    isSidebarCollapsed.value = readSidebarPreference()
    syncShellClass(isSidebarCollapsed, isMobileMenuOpen)
    window.addEventListener('keydown', handleKeydown)
  })

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') window.removeEventListener('keydown', handleKeydown)
  })

  return {
    closeMobileMenu,
    isMobileMenuOpen,
    isSidebarCollapsed,
    openMobileMenu,
    toggleSidebar,
  }
}
