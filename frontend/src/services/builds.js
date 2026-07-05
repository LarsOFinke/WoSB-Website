import { deleteRequest, get, post } from './api'

function buildQuery(search = '', buildType = '') {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (buildType) params.set('build_type', buildType)
  return params.toString() ? `?${params.toString()}` : ''
}

export function listBuilds(search = '', buildType = '') {
  return get(`/builds${buildQuery(search, buildType)}`)
}

export function listMyBuilds(search = '', buildType = '') {
  return get(`/builds/mine${buildQuery(search, buildType)}`)
}

export function deleteMyBuild(id) {
  return deleteRequest(`/builds/mine/${id}`)
}

export function getBuild(id) {
  return get(`/builds/${id}`)
}

export function getBuildOptions() {
  return get('/builds/options')
}

export function createBuild(payload) {
  return post('/builds', payload)
}
