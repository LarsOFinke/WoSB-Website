const EMBED_PATTERN = /\[\[file:(\d+)(?:\|([a-z0-9_-]+))?\]\]/gi
const ALLOWED_EMBED_SIZES = new Set(['small', 'medium', 'large', 'full'])
const DEFAULT_EMBED_SIZE = 'large'

function normalizeSize(size) {
  const normalized = String(size || '').trim().toLowerCase()
  return ALLOWED_EMBED_SIZES.has(normalized) ? normalized : DEFAULT_EMBED_SIZE
}

export function createEmbedToken(fileId, size = DEFAULT_EMBED_SIZE) {
  return `[[file:${Number(fileId)}|${normalizeSize(size)}]]`
}

export function parseRichTextEmbeds(text = '') {
  const value = String(text || '')
  const parts = []
  let lastIndex = 0
  let match

  EMBED_PATTERN.lastIndex = 0
  while ((match = EMBED_PATTERN.exec(value)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', text: value.slice(lastIndex, match.index) })
    }
    parts.push({
      type: 'embed',
      fileId: Number(match[1]),
      size: normalizeSize(match[2]),
      raw: match[0],
    })
    lastIndex = EMBED_PATTERN.lastIndex
  }

  if (lastIndex < value.length) {
    parts.push({ type: 'text', text: value.slice(lastIndex) })
  }

  return parts.length ? parts : [{ type: 'text', text: value }]
}

export function embeddedFileIds(text = '') {
  return [...new Set(parseRichTextEmbeds(text).filter((part) => part.type === 'embed').map((part) => part.fileId))]
}

export function unembeddedAttachments(attachments = [], text = '') {
  const usedIds = new Set(embeddedFileIds(text))
  return (attachments || []).filter((file) => !usedIds.has(Number(file.id)))
}

export const embedSizes = ['small', 'medium', 'large', 'full']
