import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

export function listWarehouseEntries(filters = {}) {
  return get(withQuery('/admin/warehouse', filters))
}

export function createWarehouseEntry(payload) {
  return post('/admin/warehouse', payload)
}

export function updateWarehouseEntry(id, payload) {
  return put(`/admin/warehouse/${id}`, payload)
}

export function deleteWarehouseEntry(id, version) {
  return deleteRequest(withQuery(`/admin/warehouse/${id}`, { version }))
}

export function listWarehouseFleets() {
  return get('/fleets')
}

export function listWarehouseMembers(fleetId) {
  return get(withQuery('/admin/users', {
    fleet_id: fleetId,
    status: 'active',
    limit: 500,
  }))
}
