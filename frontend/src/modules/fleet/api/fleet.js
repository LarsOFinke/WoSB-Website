import { get, post, put } from '@/shared/api/client'

export const FLEET_FOCUS_VALUES = [
  'trade',
  'faction',
  'port_battle',
  'training',
  'farming',
  'recon',
  'support',
  'mixed',
]
export const FLEET_ROLES = ['member', 'fleet_lieutenant', 'fleet_admiral']
export const FLEET_MEMBER_STATUSES = ['pending', 'active', 'inactive']

export function listFleets() {
  return get('/fleets')
}

export function listManageableFleets() {
  return get('/fleets/manageable')
}

export function listMyFleetMemberships() {
  return get('/fleets/memberships/me')
}

export function getFleet(id) {
  return get(`/fleets/${id}`)
}

export function getFleetManagementDetail(id) {
  return get(`/fleets/${id}/manage`)
}

export function getPublicOfficialFleet() {
  return get('/fleets/public/official')
}

export async function getOfficialFleet() {
  const fleets = await listFleets()
  return fleets[0] || null
}

export async function getOfficialFleetManagementDetail() {
  const fleets = await listManageableFleets()
  if (!fleets.length) return null
  return getFleetManagementDetail(fleets[0].id)
}

export function createFleet(payload) {
  return post('/fleets', payload)
}

export function updateFleet(id, payload) {
  return put(`/fleets/${id}`, payload)
}

export function joinFleet(payload = {}) {
  return post('/fleets/join', payload)
}

export function updateFleetMembership(fleetId, membershipId, payload) {
  return put(`/fleets/${fleetId}/memberships/${membershipId}`, payload)
}
