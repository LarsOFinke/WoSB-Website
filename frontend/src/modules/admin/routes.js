export const adminRoutes = [
  {
    path: '/admin/bot-setup',
    name: 'admin-bot-setup',
    component: () => import('./pages/BotSetupPage.vue'),
    meta: { requiresAdmin: true, titleKey: 'botSetup.title' },
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
