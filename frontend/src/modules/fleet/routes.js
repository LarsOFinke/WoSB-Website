export const fleetRoutes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('./pages/LandingPage.vue'),
    meta: { public: true, titleKey: 'common.home' },
  },
  { path: '/home', redirect: '/' },
  {
    path: '/fleet',
    name: 'public-fleet',
    component: () => import('./pages/FleetPublicPage.vue'),
    meta: { public: true, titleKey: 'common.fleetOverview' },
  },
  {
    path: '/fleets',
    name: 'fleets',
    component: () => import('./pages/FleetManagePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.fleetManagement' },
  },
  { path: '/fleets/manage', redirect: '/fleets' },
]
