import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const SIDEBAR_STORAGE_KEY = 'blackwater-hub.sidebar.collapsed'

function syncShellClass(isSidebarCollapsed, isMobileMenuOpen) {
  if (typeof document === 'undefined') return
  document.body.classList.toggle('sidebar-collapsed', isSidebarCollapsed.value)
  document.body.classList.toggle('mobile-sidebar-open', isMobileMenuOpen.value)
}

function readSidebarPreference() {
  if (typeof localStorage === 'undefined') return false
  return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true'
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

  watch(() => route.fullPath, closeMobileMenu)

  onMounted(() => {
    isSidebarCollapsed.value = readSidebarPreference()
    syncShellClass(isSidebarCollapsed, isMobileMenuOpen)
  })

  return {
    closeMobileMenu,
    isMobileMenuOpen,
    isSidebarCollapsed,
    openMobileMenu,
    toggleSidebar,
  }
}
