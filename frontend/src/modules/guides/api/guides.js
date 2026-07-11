import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

export function listGuides(search = '', category = '') {
  return get(withQuery('/guides', { search, category }))
}

export function getGuide(id) {
  return get(`/guides/${id}`)
}

export function createGuide(payload) {
  return post('/guides', payload)
}

export function updateGuide(id, payload) {
  return put(`/guides/${id}`, payload)
}

export function deleteGuide(id) {
  return deleteRequest(`/guides/${id}`)
}
