export function isoDate(value) {
  return value.toISOString().slice(0, 10)
}

export function shiftDate(value, days) {
  const shifted = new Date(value)
  shifted.setDate(shifted.getDate() + days)
  return shifted
}

export function filterAdminBuilds(builds, { rate = '', visibility = '' } = {}) {
  return builds.filter((build) => {
    if (rate && String(build.ship?.rate || '') !== String(rate)) return false
    if (visibility === 'official' && !build.is_official_template) return false
    if (visibility === 'community' && build.is_official_template) return false
    return true
  })
}

export function filterAdminUsers(users, { search = '', role = '', status = '' } = {}) {
  const term = search.trim().toLowerCase()
  return users.filter((row) => {
    if (term && !`${row.username} ${row.display_name}`.toLowerCase().includes(term)) return false
    if (role && row.role !== role) return false
    if (status === 'active' && !row.is_active) return false
    if (status === 'inactive' && row.is_active) return false
    return true
  })
}

export function filterAndSortEvents(events, search = '') {
  const term = search.trim().toLowerCase()
  return [...events]
    .filter((event) => !term || `${event.title} ${event.location || ''} ${event.description || ''}`.toLowerCase().includes(term))
    .sort((left, right) => new Date(left.start_at) - new Date(right.start_at))
}

export function ownerMatches(row, search = '') {
  const term = search.trim().toLowerCase()
  if (!term) return true
  return `${row.owner?.display_name || ''} ${row.owner?.username || ''}`.toLowerCase().includes(term)
}

export function countVisibleContent(scope, collections) {
  if (scope === 'forum') return collections.forum.length
  if (scope === 'guides') return collections.guides.length
  if (scope === 'groups') return collections.groups.length
  return collections.forum.length + collections.guides.length + collections.groups.length
}

export function crewTotal(build) {
  return Number(build.sailors) + Number(build.soldiers) + Number(build.musketeers) + Number(build.mercenaries)
}

export function formatDuration(value) {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value)} ms`
}

export function calendarRequestRange(fromDate, toDate, fallbackDays = 90) {
  const start = fromDate ? new Date(`${fromDate}T00:00:00`) : new Date()
  start.setHours(0, 0, 0, 0)
  const end = toDate ? new Date(`${toDate}T23:59:59`) : shiftDate(start, fallbackDays)
  return { start: start.toISOString(), end: end.toISOString() }
}
