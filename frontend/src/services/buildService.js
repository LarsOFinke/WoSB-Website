import { apiClient } from './apiClient'

export const buildService = {
  async list() {
    const { data } = await apiClient.get('/builds')
    return data
  },

  async get(id) {
    const { data } = await apiClient.get(`/builds/${id}`)
    return data
  },

  async create(payload) {
    const { data } = await apiClient.post('/builds', payload)
    return data
  },

  async listOptions(params = {}) {
    const { data } = await apiClient.get('/builds/options/catalog', { params })
    return data
  },
}
