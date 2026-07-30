export const adminRoutes = [
  {
    path: '/admin/legal-notice',
    name: 'admin-legal-notice',
    component: () => import('@/modules/legal/pages/LegalNoticeAdminPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'legalNotice.admin.title' },
  },
  {
    path: '/admin/database-backups',
    name: 'admin-database-backups',
    component: () => import('./pages/DatabaseBackupsPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'admin.backups.title' },
  },
  {
    path: '/admin/discord-broadcasts',
    name: 'admin-discord-broadcasts',
    component: () => import('./pages/DiscordBroadcastsPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'admin.webhooks.broadcast.pageTitle' },
  },
  {
    path: '/admin/discord-webhooks',
    name: 'admin-discord-webhooks',
    component: () => import('./pages/DiscordWebhooksPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'webhookSetup.title' },
  },
  {
    path: '/admin/master-data',
    name: 'admin-master-data',
    component: () => import('./pages/MasterDataPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'masterData.title' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('./pages/AdminPage.vue'),
    meta: { requiresStaff: true, titleKey: 'common.staffPanel' },
  },
]
