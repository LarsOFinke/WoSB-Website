function xmlAttributeValue(value) {
  return String(value || '')
    .replaceAll('&amp;', '&')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunkSize = 0x8000
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))
  }
  return btoa(binary)
}

function blobToDataUrl(blob) {
  if (typeof FileReader === 'function') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result || ''))
      reader.onerror = () => reject(reader.error || new Error('Print image could not be read.'))
      reader.readAsDataURL(blob)
    })
  }
  return blob.arrayBuffer().then((buffer) => {
    const mimeType = String(blob.type || 'application/octet-stream').split(';')[0].trim() || 'application/octet-stream'
    return `data:${mimeType};${'base64,'}${arrayBufferToBase64(buffer)}`
  })
}

async function fetchPrintImageDataUrl(url, fetchImpl) {
  const response = await fetchImpl(url, {
    credentials: 'same-origin',
    cache: 'no-store',
    mode: 'same-origin',
  })
  if (!response?.ok) throw new Error(`Print image request failed (${response?.status || 'network'}): ${url}`)
  const blob = await response.blob()
  if (!blob?.size) throw new Error(`Print image response was empty: ${url}`)
  return blobToDataUrl(blob)
}

function loadHtmlImage(url, ImageImpl) {
  return new Promise((resolve, reject) => {
    const image = new ImageImpl()
    let settled = false
    const finish = (callback, value) => {
      if (settled) return
      settled = true
      image.onload = null
      image.onerror = null
      callback(value)
    }
    image.onload = () => finish(resolve, image)
    image.onerror = () => finish(reject, new Error(`Print image element failed to load: ${url}`))
    image.decoding = 'async'
    image.src = url
    if (image.complete && image.naturalWidth > 0) finish(resolve, image)
  })
}

async function rasterizePrintImageDataUrl(url, { ImageImpl = globalThis.Image, documentObject = globalThis.document } = {}) {
  if (typeof ImageImpl !== 'function' || !documentObject?.createElement) {
    throw new Error('Print image raster fallback is unavailable.')
  }
  const image = await loadHtmlImage(url, ImageImpl)
  const width = Math.max(1, Number(image.naturalWidth || image.width || 96))
  const height = Math.max(1, Number(image.naturalHeight || image.height || 96))
  const canvas = documentObject.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext?.('2d')
  if (!context) throw new Error('Print image raster fallback has no canvas context.')
  context.drawImage(image, 0, 0, width, height)
  const dataUrl = canvas.toDataURL?.('image/png') || ''
  if (!dataUrl.startsWith('data:image/')) throw new Error('Print image raster fallback could not encode the image.')
  return dataUrl
}

async function resolvePrintImageDataUrl(url, options = {}) {
  const errors = []
  if (typeof options.fetchImpl === 'function') {
    try {
      return await fetchPrintImageDataUrl(url, options.fetchImpl)
    } catch (error) {
      errors.push(error)
    }
  }
  try {
    return await rasterizePrintImageDataUrl(url, options)
  } catch (error) {
    errors.push(error)
  }
  const error = new Error(`Print image could not be embedded: ${url}`)
  error.causes = errors
  throw error
}

export async function inlinePrintImageResources(svg, {
  fetchImpl = typeof globalThis.fetch === 'function' ? globalThis.fetch.bind(globalThis) : null,
  ImageImpl = globalThis.Image,
  documentObject = globalThis.document,
  cache = new Map(),
} = {}) {
  const hrefs = [...String(svg || '').matchAll(/\bhref="([^"]+)"/g)]
    .map((match) => match[1])
    .filter((href, index, values) => values.indexOf(href) === index)
  const externalHrefs = hrefs.filter((href) => /^https?:\/\//i.test(xmlAttributeValue(href)))
  if (!externalHrefs.length) return svg

  const replacements = new Map()
  const failures = []
  await Promise.all(externalHrefs.map(async (escapedHref) => {
    const href = xmlAttributeValue(escapedHref)
    let task = cache.get(href)
    if (!task) {
      task = resolvePrintImageDataUrl(href, { fetchImpl, ImageImpl, documentObject })
      cache.set(href, task)
    }
    try {
      replacements.set(escapedHref, await task)
    } catch (error) {
      cache.delete(href)
      failures.push({ href, error })
    }
  }))

  if (failures.length) {
    const failedUrls = failures.map(({ href }) => href).join(', ')
    console.error('Build print image embedding failed.', failures)
    throw new Error(`Build print image embedding failed for: ${failedUrls}`)
  }

  return externalHrefs.reduce(
    (result, escapedHref) => result.replaceAll(`href="${escapedHref}"`, `href="${replacements.get(escapedHref)}"`),
    svg,
  )
}
