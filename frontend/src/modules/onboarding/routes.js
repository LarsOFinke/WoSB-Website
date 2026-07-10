export const onboardingRoutes = [
  {
    path: '/new-captain',
    name: 'new-captain-guide',
    component: () => import('./pages/NewcomerGuidePage.vue'),
    meta: { requiresUser: true, titleKey: 'newcomerGuide.title' },
  },
]
