function workspaceItem(key, icon, label) {
  return {
    key,
    icon,
    label,
    to: key === 'overview' ? '/admin' : { path: '/admin', query: { section: key } },
  }
}

export function createStaffNavigationGroups(t, { isAdmin = false } = {}) {
  const groups = [
    {
      key: 'moderation',
      label: t('admin.workspace.navigation.workspace'),
      items: [
        workspaceItem('overview', 'compass', t('admin.tabs.overview')),
        workspaceItem('registrations', 'inbox', t('admin.tabs.registrations')),
        workspaceItem('calendar', 'calendar', t('admin.tabs.calendar')),
        workspaceItem('content', 'forum', t('admin.tabs.content')),
      ],
    },
    {
      key: 'operations',
      label: t('admin.workspace.navigation.operations'),
      items: [
        workspaceItem('builds', 'builds', t('admin.tabs.builds')),
        ...(isAdmin ? [
          workspaceItem('status', 'activity', t('admin.tabs.status')),
          workspaceItem('logs', 'activity', t('admin.tabs.logs')),
          workspaceItem('ip-blocks', 'lock', t('admin.tabs.ipBlocks')),
          workspaceItem('audit', 'inbox', t('admin.tabs.audit')),
        ] : []),
      ],
    },
    {
      key: 'administration',
      label: t('admin.workspace.navigation.administration'),
      items: isAdmin ? [
        workspaceItem('users', 'users', t('admin.tabs.users')),
        { key: 'master-data', icon: 'builds', label: t('masterData.title'), to: '/admin/master-data', protected: true },
        { key: 'legal-notice', icon: 'inbox', label: t('legalNotice.admin.navigation'), to: '/admin/legal-notice', protected: true },
        { key: 'webhooks', icon: 'webhook', label: t('webhookSetup.title'), to: '/admin/discord-webhooks', protected: true },
        { key: 'raid-helper', icon: 'calendar', label: t('raidHelper.title'), to: '/admin/raid-helper', protected: true },
        { key: 'broadcasts', icon: 'send', label: t('admin.webhooks.broadcast.pageTitle'), to: '/admin/discord-broadcasts', protected: true },
        { key: 'backups', icon: 'database', label: t('admin.backups.title'), to: '/admin/database-backups', protected: true },
      ] : [],
    },
  ]

  return groups.filter((group) => group.items.length)
}

export function staffNavigationLabel(groups, activeKey) {
  return groups.flatMap((group) => group.items).find((item) => item.key === activeKey)?.label || ''
}
