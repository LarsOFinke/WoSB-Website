import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

export const SQUAD_ROLES = ['member', 'officer', 'leader']

export function listSquads({ includeInactive = false } = {}) {
  return get(withQuery('/squads', { include_inactive: includeInactive || '' }))
}

export function getSquad(id) {
  return get(`/squads/${id}`)
}

export function listSquadRoster() {
  return get('/squads/roster')
}

export function createSquad(payload) {
  return post('/squads', payload)
}

export function updateSquad(id, payload) {
  return put(`/squads/${id}`, payload)
}

export function archiveSquad(id) {
  return deleteRequest(`/squads/${id}`)
}

export function addSquadMember(id, payload) {
  return post(`/squads/${id}/members`, payload)
}

export function updateSquadMember(id, memberId, payload) {
  return put(`/squads/${id}/members/${memberId}`, payload)
}

export function removeSquadMember(id, memberId) {
  return deleteRequest(`/squads/${id}/members/${memberId}`)
}
