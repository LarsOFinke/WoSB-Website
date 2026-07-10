export const buildRoutes = [
  {
    path: '/builds',
    name: 'builds',
    component: () => import('./pages/BuildListPage.vue'),
    meta: { public: true },
  },
  {
    path: '/builds/new',
    name: 'builds-new',
    component: () => import('./pages/BuildCreatePage.vue'),
    meta: { requiresUser: true },
  },
  {
    path: '/builds/:id',
    name: 'builds-detail',
    component: () => import('./pages/BuildDetailPage.vue'),
    props: true,
    meta: { public: true },
  },
  {
    path: '/profile/builds',
    name: 'my-builds',
    component: () => import('./pages/MyBuildsPage.vue'),
    meta: { requiresUser: true },
  },
]
