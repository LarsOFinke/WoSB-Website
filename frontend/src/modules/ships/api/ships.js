import { get } from '@/shared/api/client'

export function listShips() {
  return get('/ships')
}
