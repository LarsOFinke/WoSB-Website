export const fleetRoutes = [
  {
    path: '/',
    name: 'fleet-portal',
    component: () => import('./pages/FleetListPage.vue'),
    meta: { public: true, titleKey: 'common.home' },
  },
  { path: '/home', redirect: '/' },
  {
    path: '/fleets',
    name: 'fleets',
    component: () => import('./pages/FleetManagePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.fleetManagement' },
  },
  { path: '/fleets/manage', redirect: '/fleets' },
]
