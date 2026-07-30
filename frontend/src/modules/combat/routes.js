export const combatRoutes = [
  {
    path: '/combat-analysis',
    name: 'combat-analysis',
    component: () => import('./pages/CombatAnalysisPage.vue'),
    meta: { requiresUser: true, titleKey: 'combatAnalysis.title' },
  },
]
