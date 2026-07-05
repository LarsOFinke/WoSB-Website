import { get, post } from './api'

function buildQuery({ search = '', focus = '', minShipRate = '', maxShipRate = '' } = {}) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (focus) params.set('focus', focus)
  if (minShipRate) params.set('min_ship_rate', minShipRate)
  if (maxShipRate) params.set('max_ship_rate', maxShipRate)
  return params.toString() ? `?${params.toString()}` : ''
}

export function listGroups(filters = {}) {
  return get(`/groups${buildQuery(filters)}`)
}

export function listMyGroups(search = '') {
  return get(`/groups/mine${buildQuery({ search })}`)
}

export function getGroup(id) {
  return get(`/groups/${id}`)
}

export function createGroup(payload) {
  return post('/groups', payload)
}

export function joinGroup(id, payload) {
  return post(`/groups/${id}/join`, payload)
}

export function closeGroup(id) {
  return post(`/groups/${id}/close`, {})
}
