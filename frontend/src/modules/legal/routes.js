export const legalRoutes = [
  {
    path: '/impressum',
    name: 'legal-notice',
    component: () => import('./pages/LegalNoticePage.vue'),
    meta: { titleKey: 'legalNotice.public.title' },
  },
]
