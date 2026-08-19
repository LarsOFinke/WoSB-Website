export const warehouseRoutes = [
  {
    path: '/admin/warehouse',
    name: 'admin-warehouse',
    component: () => import('./pages/WarehousePage.vue'),
    meta: { requiresAdmin: true, titleKey: 'warehouse.title' },
  },
]
