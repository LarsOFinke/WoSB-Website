import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

export function listWarehouseEntries(filters = {}) {
  return get(withQuery('/warehouse', filters))
}

export function listWarehousePorts() {
  return get('/warehouse/ports')
}

export function listAdminWarehousePorts() {
  return get('/admin/master-data/warehouse-ports')
}

export function createWarehousePort(payload) {
  return post('/admin/master-data/warehouse-ports', payload)
}

export function updateWarehousePort(id, payload) {
  return put(`/admin/master-data/warehouse-ports/${id}`, payload)
}

export function deactivateWarehousePort(id) {
  return deleteRequest(`/admin/master-data/warehouse-ports/${id}`)
}

export function createWarehouseEntry(payload) {
  return post('/warehouse', payload)
}

export function updateWarehouseEntry(id, payload) {
  return put(`/warehouse/${id}`, payload)
}

export function deleteWarehouseEntry(id, version) {
  return deleteRequest(withQuery(`/warehouse/${id}`, { version }))
}

export function listWarehouseFleets() {
  return get('/fleets')
}

export function listWarehouseMembers(fleetId) {
  return get(`/fleets/${fleetId}/manage`).then((fleet) => (fleet.memberships || [])
    .filter((membership) => membership.status === 'active')
    .map((membership) => membership.user))
}
