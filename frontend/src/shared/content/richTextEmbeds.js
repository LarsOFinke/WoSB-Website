const EMBED_PATTERN = /\[\[(file|build):(\d+)(?:\|([a-z0-9_-]+))?\]\]/gi
const ALLOWED_EMBED_SIZES = new Set(['small', 'medium', 'large', 'full'])
const ALLOWED_BUILD_LAYOUTS = new Set(['compact', 'card', 'full'])
const DEFAULT_EMBED_SIZE = 'large'
const DEFAULT_BUILD_LAYOUT = 'card'

function normalizeFileSize(size) {
  const normalized = String(size || '').trim().toLowerCase()
  return ALLOWED_EMBED_SIZES.has(normalized) ? normalized : DEFAULT_EMBED_SIZE
}

function normalizeBuildLayout(layout) {
  const normalized = String(layout || '').trim().toLowerCase()
  return ALLOWED_BUILD_LAYOUTS.has(normalized) ? normalized : DEFAULT_BUILD_LAYOUT
}

export function createEmbedToken(fileId, size = DEFAULT_EMBED_SIZE) {
  return `[[file:${Number(fileId)}|${normalizeFileSize(size)}]]`
}

export function createBuildEmbedToken(buildId, layout = DEFAULT_BUILD_LAYOUT) {
  return `[[build:${Number(buildId)}|${normalizeBuildLayout(layout)}]]`
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

    if (match[1].toLowerCase() === 'build') {
      parts.push({
        type: 'buildEmbed',
        buildId: Number(match[2]),
        layout: normalizeBuildLayout(match[3]),
        raw: match[0],
      })
    } else {
      parts.push({
        type: 'fileEmbed',
        fileId: Number(match[2]),
        size: normalizeFileSize(match[3]),
        raw: match[0],
      })
    }
    lastIndex = EMBED_PATTERN.lastIndex
  }

  if (lastIndex < value.length) {
    parts.push({ type: 'text', text: value.slice(lastIndex) })
  }

  return parts.length ? parts : [{ type: 'text', text: value }]
}

export function embeddedFileIds(text = '') {
  return [...new Set(parseRichTextEmbeds(text).filter((part) => part.type === 'fileEmbed').map((part) => part.fileId))]
}

export function embeddedBuildIds(text = '') {
  return [...new Set(parseRichTextEmbeds(text).filter((part) => part.type === 'buildEmbed').map((part) => part.buildId))]
}

export function unembeddedAttachments(attachments = [], text = '') {
  const usedIds = new Set(embeddedFileIds(text))
  return (attachments || []).filter((file) => !usedIds.has(Number(file.id)))
}

export function unembeddedBuilds(builds = [], text = '') {
  const usedIds = new Set(embeddedBuildIds(text))
  return (builds || []).filter((build) => !usedIds.has(Number(build.id)))
}

export function removeFileEmbedTokens(text = '', fileId) {
  const id = Number(fileId)
  if (!id) return text
  return String(text || '').replace(new RegExp(`\\n?\\n?\\[\\[file:${id}(?:\\|[a-z0-9_-]+)?\\]\\]\\n?\\n?`, 'gi'), '\n\n').trim()
}

export function removeBuildEmbedTokens(text = '', buildId) {
  const id = Number(buildId)
  if (!id) return text
  return String(text || '').replace(new RegExp(`\\n?\\n?\\[\\[build:${id}(?:\\|[a-z0-9_-]+)?\\]\\]\\n?\\n?`, 'gi'), '\n\n').trim()
}

export const embedSizes = ['small', 'medium', 'large', 'full']
export const buildEmbedLayouts = ['compact', 'card', 'full']
