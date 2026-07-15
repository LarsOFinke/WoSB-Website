const DEFAULT_MANAGEMENT = Object.freeze({
  can_edit_directory: false,
  can_change_role: false,
  can_change_status: false,
  assignable_roles: [],
  protected: true,
  reason: 'insufficient',
})

export function membershipManagement(membership) {
  return membership?.management || DEFAULT_MANAGEMENT
}

export function filterFleetMemberships(memberships, { search = '', status = '', role = '' } = {}) {
  const query = search.trim().toLowerCase()
  return memberships.filter((membership) => {
    if (status && membership.status !== status) return false
    if (role && membership.role !== role) return false

    const searchable = [
      membership.user?.display_name,
      membership.user?.username,
      membership.user?.role,
      membership.note,
      membership.assignment,
      membership.availability,
      membership.preferred_ships,
      membership.timezone,
      membership.discord_handle,
      membership.admin_note,
    ].filter(Boolean).join(' ').toLowerCase()

    return !query || searchable.includes(query)
  })
}

export function isFleetLeadership(membership) {
  return membership?.status === 'active' && ['fleet_admiral', 'fleet_lieutenant'].includes(membership.role)
}

export function hasFleetMemberPermission(membership) {
  const management = membershipManagement(membership)
  return management.can_edit_directory || management.can_change_role || management.can_change_status
}

export function membershipFieldPayload(field, value) {
  return { [field]: value || null }
}
