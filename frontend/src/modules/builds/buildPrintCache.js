import {
  BUILD_PRINT_RENDERER_VERSION,
  buildPrintFileName,
  createBuildPrintDocument,
} from './buildPrintExport.js'
import { triggerPrintDownload } from '../../shared/printing/printDocument.js'

async function sha256Hex(value) {
  const cryptoObject = globalThis.crypto
  if (!cryptoObject?.subtle) throw new Error('Web Crypto is unavailable for the build print cache key.')
  const bytes = new TextEncoder().encode(String(value || ''))
  const digest = await cryptoObject.subtle.digest('SHA-256', bytes)
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

export async function createBuildPrintCacheDescriptor(build, helpers = {}) {
  const document = createBuildPrintDocument(build, helpers)
  const digest = await sha256Hex(`${BUILD_PRINT_RENDERER_VERSION}\0${document.svg}`)
  return {
    cacheKey: `print-v${BUILD_PRINT_RENDERER_VERSION}:${digest}`,
    sourceUpdatedAt: String(build?.updated_at || ''),
  }
}

export function downloadBuildPrintPngBlob(build, blob) {
  triggerPrintDownload(blob, buildPrintFileName(build, 'png'))
}

export async function fetchBuildPrintPngBlob(url, fetchImpl = globalThis.fetch?.bind(globalThis)) {
  if (!fetchImpl) throw new Error('Fetch is unavailable for the cached build image.')
  const response = await fetchImpl(url, { credentials: 'include', cache: 'force-cache' })
  if (!response.ok) throw new Error(`Cached build image request failed (${response.status}).`)
  return response.blob()
}

export async function downloadBuildPrintPngFromUrl(build, url, fetchImpl = globalThis.fetch?.bind(globalThis)) {
  downloadBuildPrintPngBlob(build, await fetchBuildPrintPngBlob(url, fetchImpl))
}
