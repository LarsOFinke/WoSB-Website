import { deleteRequest, get, post } from './api'
import { withQuery } from './query'

export function listAdminBuilds(search = '', buildType = '') {
  return get(withQuery('/admin/builds', { search, build_type: buildType }))
}

export function deleteAdminBuild(id) {
  return deleteRequest(`/admin/builds/${id}`)
}

export function listUsers() {
  return get('/admin/users')
}

export function createModerator(payload) {
  return post('/admin/moderators', payload)
}
