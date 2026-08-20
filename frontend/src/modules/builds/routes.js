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
    meta: { requiresContentAuthor: true, titleKey: 'common.builds' },
  },
  {
    path: '/builds/:id/edit',
    name: 'builds-edit',
    component: () => import('./pages/BuildCreatePage.vue'),
    props: true,
    meta: { requiresContentAuthor: true, titleKey: 'builds.edit.title' },
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
    meta: { requiresContentAuthor: true, titleKey: 'common.builds' },
  },
]
