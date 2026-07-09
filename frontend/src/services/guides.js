import { deleteRequest, get, post } from './api'
import { withQuery } from './query'

export function listGuides(search = '', category = '') {
  return get(withQuery('/guides', { search, category }))
}

export function getGuide(id) {
  return get(`/guides/${id}`)
}

export function createGuide(payload) {
  return post('/guides', payload)
}

export function deleteGuide(id) {
  return deleteRequest(`/guides/${id}`)
}
