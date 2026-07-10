export function createWorkspaceLinks(t, { isAuthenticated = false, isStaff = false } = {}) {
  const publicLinks = [
    { to: '/', label: t('common.home'), icon: '⌂', exact: true },
    { to: '/builds', label: t('common.builds'), icon: '⚙' },
  ]

  if (!isAuthenticated) return publicLinks

  const memberLinks = [
    { to: '/guides', label: t('common.guides'), icon: '☰' },
    { to: '/groups', label: t('common.groups'), icon: '◈' },
    { to: '/calendar', label: t('common.calendar'), icon: '□' },
    { to: '/forum', label: t('common.forum'), icon: '✦' },
    { to: '/fleets', label: t('common.fleetManagement'), icon: '△' },
  ]

  if (isStaff) memberLinks.push({ to: '/admin', label: t('common.staffPanel'), icon: '◆' })
  return [...publicLinks, ...memberLinks]
}
