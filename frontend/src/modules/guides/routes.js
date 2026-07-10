export const guideRoutes = [
  {
    path: '/guides',
    name: 'guides',
    component: () => import('./pages/GuideListPage.vue'),
    meta: { requiresUser: true },
  },
  {
    path: '/guides/new',
    name: 'guides-new',
    component: () => import('./pages/GuideCreatePage.vue'),
    meta: { requiresUser: true },
  },
  {
    path: '/guides/:id',
    name: 'guides-detail',
    component: () => import('./pages/GuideDetailPage.vue'),
    props: true,
    meta: { requiresUser: true },
  },
]
