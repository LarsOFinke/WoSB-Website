export const IMAGE_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/svg+xml',
]

export const ACCEPTED_FILE_TYPES = [
  ...IMAGE_MIME_TYPES,
  'video/mp4',
  'video/webm',
  'video/quicktime',
  'application/pdf',
  'text/plain',
]

export const ACCEPT_ATTRIBUTE = ACCEPTED_FILE_TYPES.join(',')
export const MAX_UPLOAD_BYTES = 80 * 1024 * 1024
export const MAX_IMAGE_BYTES = 12 * 1024 * 1024
export const MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
