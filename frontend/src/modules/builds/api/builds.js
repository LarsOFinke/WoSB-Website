import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

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

export function getBuildOptions(shipId = null) {
  return get(withQuery('/builds/options', { ship_id: shipId || '' }))
}

export function createBuild(payload) {
  return post('/builds', payload)
}

export function updateMyBuild(id, payload) {
  return put(`/builds/mine/${id}`, payload)
}
