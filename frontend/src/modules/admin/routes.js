export const adminRoutes = [
  {
    path: '/admin/master-data',
    name: 'admin-master-data',
    component: () => import('./pages/MasterDataPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'masterData.title' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('./pages/AdminPage.vue'),
    meta: { requiresStaff: true, titleKey: 'common.staffPanel' },
  },
]
