import { createRouter, createWebHistory } from 'vue-router'

import AdminPage from '@/pages/AdminPage.vue'
import HomePage from '@/pages/HomePage.vue'
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
import { loadSession, useSession } from '@/services/session'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'home', component: HomePage },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/register', name: 'register', component: RegisterPage },
  { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresUser: true } },
  { path: '/profile/builds', name: 'my-builds', component: MyBuildsPage, meta: { requiresUser: true } },
  { path: '/profile/groups', name: 'my-groups', component: MyGroupsPage, meta: { requiresUser: true } },
  { path: '/admin', name: 'admin', component: AdminPage, meta: { requiresStaff: true } },
  { path: '/builds', name: 'builds', component: BuildListPage },
  { path: '/groups', name: 'groups', component: GroupListPage },
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
