export const privacyRoutes = [
  {
    path: '/privacy',
    name: 'privacy-center',
    component: () => import('./pages/PrivacyCenterPage.vue'),
    meta: { titleKey: 'privacy.center.title' },
  },
]
