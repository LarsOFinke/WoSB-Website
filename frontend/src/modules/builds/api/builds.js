import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

function buildFilters(search = '', buildType = '', classification = '') {
  return { search, build_type: buildType, classification }
}

export function listBuilds(search = '', buildType = '', classification = '') {
  return get(withQuery('/builds', buildFilters(search, buildType, classification)))
}

export function listMyBuilds(search = '', buildType = '', classification = '') {
  return get(withQuery('/builds/mine', buildFilters(search, buildType, classification)))
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

export function listBuildRoles() {
  return get('/builds/roles')
}

export function addBuildUpvote(id) {
  return post(`/builds/${id}/upvote`, {})
}

export function removeBuildUpvote(id) {
  return deleteRequest(`/builds/${id}/upvote`)
}

export function createBuild(payload) {
  return post('/builds', payload)
}

export function updateMyBuild(id, payload) {
  return put(`/builds/mine/${id}`, payload)
}
