import { deleteRequest, get, post } from './api'
import { withQuery } from './query'

function buildFilters(search = '', buildType = '') {
  return { search, build_type: buildType }
}

export function listBuilds(search = '', buildType = '') {
  return get(withQuery('/builds', buildFilters(search, buildType)))
}

export function listMyBuilds(search = '', buildType = '') {
  return get(withQuery('/builds/mine', buildFilters(search, buildType)))
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
