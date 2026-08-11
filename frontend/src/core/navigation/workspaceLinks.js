export function createWorkspaceLinks(t, { isAuthenticated = false, isStaff = false, isAdmin = false, canManageFleet = false } = {}) {
  const publicLinks = [
    { to: '/', label: t('common.home'), icon: 'home', exact: true, section: 'public' },
    { to: '/fleet', label: t('common.fleetOverview'), icon: 'fleet', section: 'public' },
  ]

  if (!isAuthenticated) return publicLinks

  const memberLinks = [
    { to: '/new-captain', label: t('common.newCaptainGuide'), icon: 'compass', section: 'member' },
    { to: '/builds', label: t('common.builds'), icon: 'builds', section: 'member' },
    { to: '/strategies', label: t('strategyPlanner.title'), icon: 'compass', section: 'member' },
    { to: '/combat-analysis', label: t('common.combatAnalysis'), icon: 'swords', section: 'member' },
    { to: '/guides', label: t('common.guides'), icon: 'guides', section: 'member' },
    { to: '/groups', label: t('common.groups'), icon: 'groups', section: 'member' },
    { to: '/squads', label: t('common.squads'), icon: 'users', section: 'member' },
    { to: '/calendar', label: t('common.calendar'), icon: 'calendar', section: 'member' },
    { to: '/forum', label: t('common.forum'), icon: 'forum', section: 'member' },
  ]

  if (canManageFleet) memberLinks.push({ to: '/fleets', label: t('common.fleetManagement'), icon: 'fleet', section: 'member' })
  if (isStaff) memberLinks.push({ to: '/admin', label: t('common.staffPanel'), icon: 'shield', section: 'staff' })
  if (isAdmin) {
    memberLinks.push({ to: '/admin/discord-webhooks', label: t('webhookSetup.navigation'), icon: 'webhook', section: 'staff' })
  }
  return [...publicLinks, ...memberLinks]
}


export function createPersonalLinks(t, { isAuthenticated = false } = {}) {
  if (!isAuthenticated) return []
  return [
    { to: '/profile/builds', label: t('common.myBuilds'), icon: 'builds' },
    { to: '/profile/groups', label: t('common.myGroupSearches'), icon: 'groups' },
    { to: '/profile/squads', label: t('common.mySquads'), icon: 'users' },
  ]
}
