import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'

export const FLEET_EVENT_CATEGORIES = [
  'port_battle',
  'training',
  'fleet_farm',
  'operation',
  'meeting',
  'other',
]

export function listFleetEvents(filters = {}) {
  const { start = '', end = '', category = '' } = filters
  return get(withQuery('/calendar/events', { start, end, category }))
}

export function createFleetEvent(payload) {
  return post('/calendar/events', payload)
}

export function updateFleetEvent(id, payload) {
  return put(`/calendar/events/${id}`, payload)
}

export function deleteFleetEvent(id) {
  return deleteRequest(`/calendar/events/${id}`)
}
