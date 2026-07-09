import { get, post } from './api'
import { withQuery } from './query'

function groupFilters({ search = '', focus = '', minShipRate = '', maxShipRate = '' } = {}) {
  return {
    search,
    focus,
    min_ship_rate: minShipRate,
    max_ship_rate: maxShipRate,
  }
}

export function listGroups(filters = {}) {
  return get(withQuery('/groups', groupFilters(filters)))
}

export function listMyGroups(search = '') {
  return get(withQuery('/groups/mine', { search }))
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
