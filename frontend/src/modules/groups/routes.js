export const groupRoutes = [
  {
    path: '/groups',
    name: 'groups',
    component: () => import('./pages/GroupListPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.groups' },
  },
  {
    path: '/groups/new',
    name: 'groups-new',
    component: () => import('./pages/GroupCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.groups' },
  },
  {
    path: '/groups/:id',
    name: 'groups-detail',
    component: () => import('./pages/GroupDetailPage.vue'),
    props: true,
    meta: { requiresUser: true, titleKey: 'common.groups' },
  },
  {
    path: '/profile/groups',
    name: 'my-groups',
    component: () => import('./pages/MyGroupsPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.groups' },
  },
]
