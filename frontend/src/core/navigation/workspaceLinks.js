export function createWorkspaceLinks(t, { isAuthenticated = false, isStaff = false } = {}) {
  const publicLinks = [
    { to: '/', label: t('common.home'), icon: 'home', exact: true, section: 'public' },
    { to: '/builds', label: t('common.builds'), icon: 'builds', section: 'public' },
  ]

  if (!isAuthenticated) return publicLinks

  const memberLinks = [
    { to: '/guides', label: t('common.guides'), icon: 'guides', section: 'member' },
    { to: '/groups', label: t('common.groups'), icon: 'groups', section: 'member' },
    { to: '/calendar', label: t('common.calendar'), icon: 'calendar', section: 'member' },
    { to: '/forum', label: t('common.forum'), icon: 'forum', section: 'member' },
    { to: '/fleets', label: t('common.fleetManagement'), icon: 'fleet', section: 'member' },
  ]

  if (isStaff) memberLinks.push({ to: '/admin', label: t('common.staffPanel'), icon: 'shield', section: 'staff' })
  return [...publicLinks, ...memberLinks]
}


export function createPersonalLinks(t, { isAuthenticated = false } = {}) {
  if (!isAuthenticated) return []
  return [
    { to: '/profile/builds', label: t('common.myBuilds'), icon: 'builds' },
    { to: '/profile/groups', label: t('common.myGroupSearches'), icon: 'groups' },
  ]
}
