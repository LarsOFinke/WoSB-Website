export const guideRoutes = [
  {
    path: '/guides',
    name: 'guides',
    component: () => import('./pages/GuideListPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.guides' },
  },
  {
    path: '/guides/new',
    name: 'guides-new',
    component: () => import('./pages/GuideCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.guides' },
  },
  {
    path: '/guides/:id/edit',
    name: 'guides-edit',
    component: () => import('./pages/GuideCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.guides' },
  },
  {
    path: '/guides/:id',
    name: 'guides-detail',
    component: () => import('./pages/GuideDetailPage.vue'),
    props: true,
    meta: { requiresUser: true, titleKey: 'common.guides' },
  },
]
