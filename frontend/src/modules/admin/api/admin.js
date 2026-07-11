import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'


export function getSystemUpdateStatus() {
  return get('/admin/system/update')
}

export function requestSystemUpdate(operation = 'update') {
  return post('/admin/system/update', { operation })
}

export function listRegistrationRequests(status = 'pending') {
  return get(withQuery('/admin/registration-requests', { status }))
}

export function approveRegistrationRequest(id, note = '') {
  return post(`/admin/registration-requests/${id}/approve`, { note: note || null })
}

export function rejectRegistrationRequest(id, note = '') {
  return post(`/admin/registration-requests/${id}/reject`, { note: note || null })
}

export function listAdminLogs({ level = '', path = '', limit = 120 } = {}) {
  return get(withQuery('/admin/logs', { level, path, limit }))
}

export function getAdminLogSummary() {
  return get('/admin/logs/summary')
}

export function listAdminBuilds(search = '', buildType = '') {
  return get(withQuery('/admin/builds', { search, build_type: buildType }))
}

export function deleteAdminBuild(id) {
  return deleteRequest(`/admin/builds/${id}`)
}

export function listAdminForumThreads(search = '', category = '') {
  return get(withQuery('/admin/forum/threads', { search, category }))
}

export function deleteAdminForumThread(id) {
  return deleteRequest(`/admin/forum/threads/${id}`)
}

export function listAdminGuides(search = '', category = '') {
  return get(withQuery('/admin/guides', { search, category }))
}

export function deleteAdminGuide(id) {
  return deleteRequest(`/admin/guides/${id}`)
}

export function listUsers() {
  return get('/admin/users')
}

export function createModerator(payload) {
  return post('/admin/moderators', payload)
}

export function updateUser(id, payload) {
  return put(`/admin/users/${id}`, payload)
}

export function getMasterDataOverview() {
  return get('/admin/master-data/overview')
}

export function getMasterDataTaxonomy() {
  return get('/admin/master-data/taxonomy')
}

export function listMasterDataCategories() {
  return get('/admin/master-data/categories')
}

export function createMasterDataCategory(payload) {
  return post('/admin/master-data/categories', payload)
}

export function updateMasterDataCategory(id, payload) {
  return put(`/admin/master-data/categories/${id}`, payload)
}

export function deactivateMasterDataCategory(id) {
  return deleteRequest(`/admin/master-data/categories/${id}`)
}

export function restoreMasterDataCategory(id) {
  return post(`/admin/master-data/categories/${id}/restore-seed`, {})
}

export function listMasterDataOptions({ category = '', search = '' } = {}) {
  return get(withQuery('/admin/master-data/options', { category, search }))
}

export function createMasterDataOption(payload) {
  return post('/admin/master-data/options', payload)
}

export function updateMasterDataOption(id, payload) {
  return put(`/admin/master-data/options/${id}`, payload)
}

export function deactivateMasterDataOption(id) {
  return deleteRequest(`/admin/master-data/options/${id}`)
}

export function restoreMasterDataOption(id) {
  return post(`/admin/master-data/options/${id}/restore-seed`, {})
}

export function listMasterDataShips(search = '') {
  return get(withQuery('/admin/master-data/ships', { search }))
}

export function createMasterDataShip(payload) {
  return post('/admin/master-data/ships', payload)
}

export function updateMasterDataShip(id, payload) {
  return put(`/admin/master-data/ships/${id}`, payload)
}

export function deactivateMasterDataShip(id) {
  return deleteRequest(`/admin/master-data/ships/${id}`)
}

export function restoreMasterDataShip(id) {
  return post(`/admin/master-data/ships/${id}/restore-seed`, {})
}
