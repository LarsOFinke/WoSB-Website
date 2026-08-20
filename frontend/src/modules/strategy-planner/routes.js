export const strategyRoutes = [
  {
    path: '/strategies/shared/:publicId', name: 'strategy-shared',
    component: () => import('./pages/StrategyViewPage.vue'),
    meta: { titleKey: 'strategyPlanner.title' },
  },
  {
    path: '/strategies', name: 'strategies',
    component: () => import('./pages/StrategyListPage.vue'),
    meta: { requiresUser: true, titleKey: 'strategyPlanner.title' },
  },
  {
    path: '/strategies/new', name: 'strategy-new',
    component: () => import('./pages/StrategyPlannerPage.vue'),
    meta: { requiresContentAuthor: true, titleKey: 'strategyPlanner.title' },
  },
  {
    path: '/strategies/:id/edit', name: 'strategy-edit',
    component: () => import('./pages/StrategyPlannerPage.vue'),
    meta: { requiresContentAuthor: true, titleKey: 'strategyPlanner.title' },
  },
  {
    path: '/strategies/:id', name: 'strategy-view',
    component: () => import('./pages/StrategyViewPage.vue'),
    meta: { requiresUser: true, titleKey: 'strategyPlanner.title' },
  },
]
