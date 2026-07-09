export function createWorkspaceLinks(t) {
  return [
    { to: '/home', label: t('common.home'), icon: '⌂', exact: true },
    { to: '/builds', label: t('common.builds'), icon: '⚙' },
    { to: '/guides', label: t('common.guides'), icon: '☰' },
    { to: '/groups', label: t('common.groups'), icon: '◈' },
    { to: '/calendar', label: t('common.calendar'), icon: '□' },
    { to: '/forum', label: t('common.forum'), icon: '✦' },
    { to: '/fleets', label: t('common.fleets'), icon: '△' },
  ]
}
