import { apiClient } from './apiClient'

export const shipService = {
  async list(params = {}) {
    const { data } = await apiClient.get('/ships', { params })
    return data
  },
}
