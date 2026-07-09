import { get, post } from './api'
import { withQuery } from './query'

export function listThreads(search = '', category = '') {
  return get(withQuery('/forum/threads', { search, category }))
}

export function getThread(id) {
  return get(`/forum/threads/${id}`)
}

export function createThread(payload) {
  return post('/forum/threads', payload)
}

export function createPost(threadId, payload) {
  return post(`/forum/threads/${threadId}/posts`, payload)
}
