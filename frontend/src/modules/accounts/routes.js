export const accountRoutes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./pages/LoginPage.vue'),
    meta: { guestOnly: true, titleKey: 'auth.login' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('./pages/RegisterPage.vue'),
    meta: { guestOnly: true, titleKey: 'auth.register' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('./pages/ProfilePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.profile' },
  },
]
