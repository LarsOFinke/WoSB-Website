export const fleetRoutes = [
  {
    path: '/',
    name: 'fleet-portal',
    component: () => import('./pages/FleetListPage.vue'),
    meta: { public: true },
  },
  { path: '/home', redirect: '/' },
  {
    path: '/fleets',
    name: 'fleets',
    component: () => import('./pages/FleetManagePage.vue'),
    meta: { requiresUser: true },
  },
  { path: '/fleets/manage', redirect: '/fleets' },
]
