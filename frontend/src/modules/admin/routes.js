export const adminRoutes = [
  {
    path: '/admin',
    name: 'admin',
    component: () => import('./pages/AdminPage.vue'),
    meta: { requiresStaff: true, titleKey: 'common.staffPanel' },
  },
]
