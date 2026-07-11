export const forumRoutes = [
  {
    path: '/forum',
    name: 'forum',
    component: () => import('./pages/ForumListPage.vue'),
    meta: { requiresUser: true, titleKey: 'common.forum' },
  },
  {
    path: '/forum/new',
    name: 'forum-new',
    component: () => import('./pages/ForumCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.forum' },
  },
  {
    path: '/forum/:id/edit',
    name: 'forum-edit',
    component: () => import('./pages/ForumCreatePage.vue'),
    meta: { requiresUser: true, titleKey: 'common.forum' },
  },
  {
    path: '/forum/:id',
    name: 'forum-detail',
    component: () => import('./pages/ForumDetailPage.vue'),
    props: true,
    meta: { requiresUser: true, titleKey: 'common.forum' },
  },
]
