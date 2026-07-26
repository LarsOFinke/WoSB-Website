export function stripInlineMarkdown(value) {
  return String(value || '')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_~`>#]/g, '')
    .trim()
}

export function extractGuideHeadings(body) {
  return String(body || '')
    .split(/\r?\n/)
    .map((line) => line.match(/^\s*(#{1,3})\s+(.+?)\s*#*\s*$/))
    .filter(Boolean)
    .map((match, index) => ({
      level: match[1].length,
      label: stripInlineMarkdown(match[2]),
      number: String(index + 1).padStart(2, '0'),
    }))
    .filter((heading) => heading.label)
}

export function guideHeadingNavigation(body, prefix = 'guide-section') {
  return extractGuideHeadings(body).map((heading, index) => ({
    ...heading,
    id: `${prefix}-${index + 1}`,
  }))
}

export function formatGuideDate(value, locales) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat(locales, { dateStyle: 'medium' }).format(date)
}
