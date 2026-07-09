import { get, postForm } from './api'
import { withQuery } from './query'

const EMBEDDABLE_MIME_PREFIXES = ['image/', 'video/']
const EMBEDDABLE_DOCUMENT_MIME_TYPES = new Set(['application/pdf', 'text/plain'])
export function listFiles(usageContext = '') {
  return get(withQuery('/files', { usage_context: usageContext }))
}

export function uploadFile(file, usageContext = 'general') {
  const formData = new FormData()
  formData.append('file', file)
  return postForm(withQuery('/files', { usage_context: usageContext }), formData)
}

function assetOrigin() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

  if (typeof window === 'undefined') return ''

  try {
    const resolvedApiUrl = new URL(apiBaseUrl, window.location.origin)
    return resolvedApiUrl.origin === window.location.origin ? '' : resolvedApiUrl.origin
  } catch {
    return ''
  }
}

export function absoluteFileUrl(publicUrl) {
  if (!publicUrl) return ''
  if (/^https?:\/\//i.test(publicUrl)) return publicUrl
  if (!publicUrl.startsWith('/')) return publicUrl
  return `${assetOrigin()}${publicUrl}`
}

export function fileKind(file) {
  const mimeType = String(file?.mime_type || '').toLowerCase()

  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('video/')) return 'video'
  if (mimeType === 'application/pdf') return 'pdf'
  if (mimeType === 'text/plain') return 'text'

  return 'file'
}

export function isEmbeddableFile(file) {
  const mimeType = String(file?.mime_type || '').toLowerCase()
  return EMBEDDABLE_MIME_PREFIXES.some((prefix) => mimeType.startsWith(prefix)) || EMBEDDABLE_DOCUMENT_MIME_TYPES.has(mimeType)
}

export function formatFileSize(sizeBytes) {
  const size = Number(sizeBytes || 0)
  if (!Number.isFinite(size) || size <= 0) return ''

  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unitIndex = 0

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }

  const rounded = value >= 10 || unitIndex === 0 ? Math.round(value) : value.toFixed(1)
  return `${rounded} ${units[unitIndex]}`
}
