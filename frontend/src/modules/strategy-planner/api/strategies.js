import { deleteRequest, get, post, put } from '@/shared/api/client'

export function listStrategies() { return get('/strategies') }
export function getStrategy(id) { return get(`/strategies/${id}`) }
export function getSharedStrategy(publicId) { return get(`/strategies/shared/${publicId}`) }
export function createStrategy(payload) { return post('/strategies', payload) }
export function updateStrategy(id, payload) { return put(`/strategies/${id}`, payload) }
export function deleteStrategy(id) { return deleteRequest(`/strategies/${id}`) }
export function publishStrategy(id) { return put(`/strategies/${id}/publication`, {}) }
export function unpublishStrategy(id) { return deleteRequest(`/strategies/${id}/publication`) }
