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
  const { start = '', end = '', category = '', squadId = '', fleetOnly = false } = filters
  return get(withQuery('/calendar/events', {
    start,
    end,
    category,
    squad_id: squadId,
    fleet_only: fleetOnly || '',
  }))
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

export function listRaidHelperOptions({ category, squadId = '' }) {
  return get(withQuery('/calendar/raid-helper/options', {
    category,
    squad_id: squadId,
  }))
}
