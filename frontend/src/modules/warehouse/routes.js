export const warehouseRoutes = [
  {
    path: '/warehouse',
    name: 'warehouse',
    component: () => import('./pages/WarehousePage.vue'),
    meta: { requiresUser: true, titleKey: 'warehouse.title' },
  },
]
