import { createRouter, createWebHistory } from 'vue-router'

import { loadSession, useSession } from '@/modules/accounts/session'
import { accountRoutes } from '@/modules/accounts/routes'
import { adminRoutes } from '@/modules/admin/routes'
import { buildRoutes } from '@/modules/builds/routes'
import { calendarRoutes } from '@/modules/calendar/routes'
import { fleetRoutes } from '@/modules/fleet/routes'
import { forumRoutes } from '@/modules/forum/routes'
import { groupRoutes } from '@/modules/groups/routes'
import { guideRoutes } from '@/modules/guides/routes'

const routes = [
  ...fleetRoutes,
  ...accountRoutes,
  ...buildRoutes,
  ...guideRoutes,
  ...groupRoutes,
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

router.beforeEach(async (to) => {
  const { isAuthenticated, isStaff, sessionState } = useSession()
  if (!sessionState.isReady) await loadSession()

  if (to.meta.guestOnly && isAuthenticated.value) {
    return typeof to.query.redirect === 'string' ? to.query.redirect : '/profile'
  }

  if (to.meta.requiresStaff && !isStaff.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresUser && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
