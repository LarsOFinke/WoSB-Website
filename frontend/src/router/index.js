import { createRouter, createWebHistory } from 'vue-router'

import AdminPage from '@/pages/AdminPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import MyBuildsPage from '@/pages/MyBuildsPage.vue'
import MyGroupsPage from '@/pages/MyGroupsPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'
import BuildCreatePage from '@/pages/builds/BuildCreatePage.vue'
import BuildDetailPage from '@/pages/builds/BuildDetailPage.vue'
import BuildListPage from '@/pages/builds/BuildListPage.vue'
import GroupCreatePage from '@/pages/groups/GroupCreatePage.vue'
import GroupDetailPage from '@/pages/groups/GroupDetailPage.vue'
import GroupListPage from '@/pages/groups/GroupListPage.vue'
import ForumCreatePage from '@/pages/forum/ForumCreatePage.vue'
import ForumDetailPage from '@/pages/forum/ForumDetailPage.vue'
import ForumListPage from '@/pages/forum/ForumListPage.vue'
import GuideCreatePage from '@/pages/guides/GuideCreatePage.vue'
import GuideDetailPage from '@/pages/guides/GuideDetailPage.vue'
import GuideListPage from '@/pages/guides/GuideListPage.vue'
import CalendarCreatePage from '@/pages/calendar/CalendarCreatePage.vue'
import CalendarPage from '@/pages/calendar/CalendarPage.vue'
import FleetListPage from '@/pages/fleets/FleetListPage.vue'
import FleetManagePage from '@/pages/fleets/FleetManagePage.vue'
import { loadSession, useSession } from '@/services/session'

const routes = [
  { path: '/', name: 'fleet-portal', component: FleetListPage },
  { path: '/home', redirect: '/' },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/register', name: 'register', component: RegisterPage },
  { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresUser: true } },
  { path: '/profile/builds', name: 'my-builds', component: MyBuildsPage, meta: { requiresUser: true } },
  { path: '/profile/groups', name: 'my-groups', component: MyGroupsPage, meta: { requiresUser: true } },
  { path: '/admin', name: 'admin', component: AdminPage, meta: { requiresStaff: true } },
  { path: '/builds', name: 'builds', component: BuildListPage },
  { path: '/groups', name: 'groups', component: GroupListPage },
  { path: '/forum', name: 'forum', component: ForumListPage },
  { path: '/calendar', name: 'calendar', component: CalendarPage },
  { path: '/fleets', name: 'fleets', component: FleetManagePage, meta: { requiresUser: true } },
  { path: '/fleets/manage', redirect: '/fleets' },
  { path: '/calendar/new', name: 'calendar-new', component: CalendarCreatePage, meta: { requiresStaff: true } },
  { path: '/forum/new', name: 'forum-new', component: ForumCreatePage, meta: { requiresUser: true } },
  { path: '/forum/:id', name: 'forum-detail', component: ForumDetailPage, props: true },
  { path: '/guides', name: 'guides', component: GuideListPage },
  { path: '/guides/new', name: 'guides-new', component: GuideCreatePage, meta: { requiresUser: true } },
  { path: '/guides/:id', name: 'guides-detail', component: GuideDetailPage, props: true },
  { path: '/groups/new', name: 'groups-new', component: GroupCreatePage, meta: { requiresUser: true } },
  { path: '/groups/:id', name: 'groups-detail', component: GroupDetailPage, props: true },
  { path: '/builds/new', name: 'builds-new', component: BuildCreatePage, meta: { requiresUser: true } },
  { path: '/builds/:id', name: 'builds-detail', component: BuildDetailPage, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresStaff && !to.meta.requiresUser) return true

  const { isAuthenticated, isStaff, sessionState } = useSession()
  if (!sessionState.isReady) {
    await loadSession()
  }

  if (to.meta.requiresStaff) {
    return isStaff.value ? true : '/login'
  }
  return isAuthenticated.value ? true : '/login'
})

export default router
