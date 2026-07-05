import { get } from './api'

export function listShips() {
  return get('/ships')
}
