export function buildShareUrl(buildId, locationObject = globalThis.location) {
  const origin = locationObject?.origin || ''
  return new URL(`/builds/${encodeURIComponent(buildId)}`, origin || 'http://localhost').toString()
}

function fallbackCopy(text) {
  if (!globalThis.document?.body) return false
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand?.('copy') === true
  textarea.remove()
  return copied
}

export async function copyBuildShareLink(buildId, dependencies = {}) {
  const locationObject = dependencies.location || globalThis.location
  const clipboard = dependencies.clipboard || globalThis.navigator?.clipboard
  const url = buildShareUrl(buildId, locationObject)
  if (clipboard?.writeText) {
    await clipboard.writeText(url)
    return url
  }
  if (!fallbackCopy(url)) throw new Error('Clipboard access is unavailable.')
  return url
}
