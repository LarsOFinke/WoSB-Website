const MARKDOWN_PATTERN = /!?(?:\[([^\]]*)\])\([^)]*\)|[`*_>#~|-]+/g

export function topicSummary(topic, fallback, maxLength = 150) {
  const source = String(topic?.body || '').replace(MARKDOWN_PATTERN, '$1').replace(/\s+/g, ' ').trim()
  const value = source || fallback
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength - 1).trimEnd()}…`
}

export function topicResourceCount(topic) {
  return Array.isArray(topic?.resources) ? topic.resources.length : 0
}

export function topicKind(topic) {
  return topic?.block_type === 'resources' ? 'resources' : 'text'
}

export function resourceIcon(resource) {
  if (resource?.resource_type === 'build') return 'builds'
  if (resource?.resource_type === 'guide') return 'guides'
  return 'arrow-right'
}
