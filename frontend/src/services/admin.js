import { deleteRequest, get, post } from './api'

export function listAdminBuilds(search = '', buildType = '') {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (buildType) params.set('build_type', buildType)
  const query = params.toString() ? `?${params.toString()}` : ''
  return get(`/admin/builds${query}`)
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
