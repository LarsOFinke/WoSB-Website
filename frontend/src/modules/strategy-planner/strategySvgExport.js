const PRESENTATION_PROPERTIES = [
  'color', 'fill', 'fill-opacity', 'stroke', 'stroke-opacity', 'stroke-width',
  'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray', 'font-family',
  'font-size', 'font-weight', 'letter-spacing', 'opacity', 'paint-order',
  'vector-effect',
]

function fileName(title) {
  const slug = String(title || 'strategy').replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase()
  return `${slug || 'strategy'}-strategy.svg`
}

function blobDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('Could not embed the strategy background.'))
    reader.readAsDataURL(blob)
  })
}

function inlinePresentation(source, clone) {
  const sourceNodes = [source, ...source.querySelectorAll('*')]
  const cloneNodes = [clone, ...clone.querySelectorAll('*')]
  sourceNodes.forEach((node, index) => {
    const target = cloneNodes[index]
    if (!target) return
    const computed = window.getComputedStyle(node)
    PRESENTATION_PROPERTIES.forEach((property) => {
      const value = computed.getPropertyValue(property)
      if (value) target.style.setProperty(property, value)
    })
  })
}

export async function createStrategySvg(source, backgroundUrl, fetchImpl = window.fetch.bind(window)) {
  if (!source) throw new Error('Strategy canvas is unavailable.')
  const clone = source.cloneNode(true)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.removeAttribute('class')
  clone.querySelectorAll('.is-selected').forEach((node) => node.classList.remove('is-selected'))
  inlinePresentation(source, clone)

  const background = clone.querySelector('image')
  if (background && backgroundUrl) {
    const response = await fetchImpl(backgroundUrl, { credentials: 'include' })
    if (!response.ok) throw new Error(`Could not load the strategy background (${response.status}).`)
    const embeddedUrl = await blobDataUrl(await response.blob())
    background.setAttribute('href', embeddedUrl)
  }
  return new XMLSerializer().serializeToString(clone)
}

export async function downloadStrategySvg(source, backgroundUrl, title) {
  const svg = await createStrategySvg(source, backgroundUrl)
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }))
  const anchor = window.document.createElement('a')
  anchor.href = url
  anchor.download = fileName(title)
  anchor.click()
  URL.revokeObjectURL(url)
}
