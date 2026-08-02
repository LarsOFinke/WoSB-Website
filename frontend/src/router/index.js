import { createRouter, createWebHistory } from 'vue-router'

import { installDeploymentChunkRecovery } from '@/core/navigation/deploymentChunkRecovery'
import { onLocaleChange, translate } from '@/locales'

import { loadSession, useSession } from '@/modules/accounts/session'
import { accountRoutes } from '@/modules/accounts/routes'
import { adminRoutes } from '@/modules/admin/routes'
import { buildRoutes } from '@/modules/builds/routes'
import { calendarRoutes } from '@/modules/calendar/routes'
import { combatRoutes } from '@/modules/combat/routes'
import { fleetRoutes } from '@/modules/fleet/routes'
import { forumRoutes } from '@/modules/forum/routes'
import { groupRoutes } from '@/modules/groups/routes'
import { guideRoutes } from '@/modules/guides/routes'
import { onboardingRoutes } from '@/modules/onboarding/routes'
import { privacyRoutes } from '@/modules/privacy/routes'
import { legalRoutes } from '@/modules/legal/routes'
import { squadRoutes } from '@/modules/squads/routes'

const routes = [
  ...fleetRoutes,
  ...accountRoutes,
  ...buildRoutes,
  ...combatRoutes,
  ...guideRoutes,
  ...onboardingRoutes,
  ...privacyRoutes,
  ...legalRoutes,
  ...groupRoutes,
  ...squadRoutes,
  ...calendarRoutes,
  ...forumRoutes,
  ...adminRoutes,
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

installDeploymentChunkRecovery(router)

router.beforeEach(async (to) => {
  const { canManageFleet, isAdmin, isAuthenticated, isStaff, sessionState } = useSession()
  if (!sessionState.isReady) await loadSession()

  if (to.meta.guestOnly && isAuthenticated.value) {
    return typeof to.query.redirect === 'string' ? to.query.redirect : '/profile'
  }

  if (to.meta.requiresAdmin && !isAdmin.value) {
    return { name: 'profile' }
  }

  if (to.meta.requiresStaff && !isStaff.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresUser && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresFleetManagement && !canManageFleet.value) {
    return { name: 'profile' }
  }

  return true
})

function updateDocumentTitle(to) {
  if (typeof document === 'undefined') return
  const label = to.meta.titleKey ? translate(to.meta.titleKey) : translate('common.projectName')
  document.title = label === translate('common.projectName') ? label : `${label} · RBF`
}

router.afterEach(updateDocumentTitle)
onLocaleChange(() => updateDocumentTitle(router.currentRoute.value))

export default router
