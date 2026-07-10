export const buildRoutes = [
  {
    path: '/builds',
    name: 'builds',
    component: () => import('./pages/BuildListPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.builds' },
  },
  {
    path: '/builds/new',
    name: 'builds-new',
    component: () => import('./pages/BuildCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.builds' },
  },
  {
    path: '/builds/:id',
    name: 'builds-detail',
    component: () => import('./pages/BuildDetailPage.vue'),
    props: true,
    meta: { requiresUser: true, titleKey: 'common.builds' },
  },
  {
    path: '/profile/builds',
    name: 'my-builds',
    component: () => import('./pages/MyBuildsPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.builds' },
  },
]
