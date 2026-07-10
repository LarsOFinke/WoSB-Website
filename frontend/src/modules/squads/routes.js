export const squadRoutes = [
  {
    path: '/squads',
    name: 'squads',
    component: () => import('./pages/SquadListPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.squads' },
  },
  {
    path: '/profile/squads',
    alias: '/my-squads',
    name: 'my-squads',
    component: () => import('./pages/MySquadsPage.vue'),
    meta: { requiresUser: true, titleKey: 'mySquads.title' },
  },
  {
    path: '/squads/new',
    name: 'squad-new',
    component: () => import('./pages/SquadCreatePage.vue'),
    meta: { requiresUser: true, requiresFleetManagement: true, titleKey: 'squads.create.title' },
  },
  {
    path: '/squads/:id',
    name: 'squad-detail',
    component: () => import('./pages/SquadDetailPage.vue'),
    props: (route) => ({ id: Number(route.params.id) }),
    meta: { requiresUser: true, titleKey: 'common.squads' },
  },
]
