import { createRouter, createWebHistory } from 'vue-router'

import { useSession } from '@/composables/useSession'
import AdminPanelPage from '@/views/AdminPanelPage.vue'
import BuildsPage from '@/views/BuildsPage.vue'
import GroupManagementPage from '@/views/GroupManagementPage.vue'
import GroupsPage from '@/views/GroupsPage.vue'
import HomePage from '@/views/HomePage.vue'
import LoginPage from '@/views/LoginPage.vue'
import ProfilePage from '@/views/ProfilePage.vue'
import RegisterPage from '@/views/RegisterPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomePage, meta: { public: true } },
    { path: '/login', name: 'login', component: LoginPage, meta: { public: true, guestOnly: true } },
    { path: '/register', name: 'register', component: RegisterPage, meta: { public: true, guestOnly: true } },
    { path: '/groups', name: 'groups', component: GroupsPage, meta: { public: true } },
    {
      path: '/group-management',
      name: 'group-management',
      component: GroupManagementPage,
      meta: { requiresAuth: true },
    },
    { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true } },
    { path: '/builds', name: 'builds', component: BuildsPage, meta: { public: true } },
    { path: '/admin', name: 'admin', component: AdminPanelPage, meta: { requiresAuth: true, requiresAdmin: true } },
  ],
})

router.beforeEach(async (to) => {
  const { isAuthenticated, isAdmin, isSessionReady, refreshSession } = useSession()

  if (!isSessionReady.value) {
    await refreshSession()
  }

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !isAdmin.value) {
    return { name: 'groups' }
  }

  if (to.meta.guestOnly && isAuthenticated.value) {
    return { name: 'groups' }
  }

  return true
})

export default router
