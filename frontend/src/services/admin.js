import { deleteRequest, get, post } from './api'
import { withQuery } from './query'

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
