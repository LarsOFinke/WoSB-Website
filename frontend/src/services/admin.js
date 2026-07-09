import { deleteRequest, get, post } from './api'
import { withQuery } from './query'

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
