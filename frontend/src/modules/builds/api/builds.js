import { deleteRequest, get, post, put, putForm } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

function buildFilters(search = '', buildType = '', classification = '', limit = 50, offset = 0) {
  return { search, build_type: buildType, classification, limit, offset }
}

export function listBuilds(search = '', buildType = '', classification = '', limit = 50, offset = 0) {
  return get(withQuery('/builds', buildFilters(search, buildType, classification, limit, offset)))
}

export function listMyBuilds(search = '', buildType = '', classification = '', limit = 50, offset = 0) {
  return get(withQuery('/builds/mine', buildFilters(search, buildType, classification, limit, offset)))
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

export function publishBuildPrintout(id, image, notifyDiscord = false) {
  const form = new FormData()
  form.append('image', image, `build-${id}.png`)
  return putForm(withQuery(`/builds/${id}/printout`, { notify_discord: notifyDiscord }), form)
}
