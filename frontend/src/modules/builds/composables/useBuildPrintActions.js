import { onBeforeUnmount, ref } from 'vue'
import {
  createBuildPrintPngBlob,
  downloadBuildPrintSvg,
  openBuildPrintWindow,
} from '@/modules/builds/buildPrintExport'
import {
  createBuildPrintCacheDescriptor,
  downloadBuildPrintPngBlob,
  downloadBuildPrintPngFromUrl,
  fetchBuildPrintPngBlob,
} from '@/modules/builds/buildPrintCache'
import { getBuild, publishBuildPrintout } from '@/modules/builds/api/builds'
import { absoluteFileUrl } from '@/modules/files/api/files'

export function useBuildPrintActions(build, { optionImage, optionLabel, t, canCache }) {
  const printStatus = ref('')
  const printPreviewUrl = ref('')
  const printPreviewOpen = ref(false)
  const printBusy = ref(false)
  let printPreviewBlob = null
  let printPreviewObjectUrl = false

  function revokePrintPreview() {
    if (printPreviewObjectUrl && printPreviewUrl.value) URL.revokeObjectURL(printPreviewUrl.value)
    printPreviewUrl.value = ''
    printPreviewBlob = null
    printPreviewObjectUrl = false
  }

  function cacheMatches(value, cache) {
    return Boolean(
      value?.printout_url
      && value?.printout_cache_key === cache.cacheKey
      && String(value?.printout_source_updated_at || '') === cache.sourceUpdatedAt,
    )
  }

  function applyPublishedCache(published) {
    if (!build.value || !published) return
    build.value.printout_url = published.url
    build.value.printout_cache_key = published.cache_key
    build.value.printout_checksum = published.checksum
    build.value.printout_source_updated_at = published.source_updated_at
  }

  async function refreshBuildForCache() {
    if (!build.value?.id) return build.value
    const refreshed = await getBuild(build.value.id)
    build.value = refreshed
    return refreshed
  }

  async function ensurePrintPreview() {
    revokePrintPreview()
    const current = await refreshBuildForCache()
    const cache = await createBuildPrintCacheDescriptor(current, { t, optionLabel, optionImage })

    if (cacheMatches(current, cache)) {
      const cachedUrl = absoluteFileUrl(current.printout_url) || current.printout_url
      try {
        const cachedImage = await fetchBuildPrintPngBlob(cachedUrl)
        printPreviewBlob = cachedImage
        printPreviewUrl.value = URL.createObjectURL(cachedImage)
        printPreviewObjectUrl = true
        printPreviewOpen.value = true
        return { cache, cached: true }
      } catch {
        // Missing filesystem cache: render locally and let an authorized owner/staff user repair it.
      }
    }

    const image = await createBuildPrintPngBlob(current, { t, optionLabel, optionImage })
    printPreviewBlob = image
    printPreviewUrl.value = URL.createObjectURL(image)
    printPreviewObjectUrl = true
    printPreviewOpen.value = true

    if (canCache?.value) {
      try {
        const published = await publishBuildPrintout(current.id, image, false, cache)
        applyPublishedCache(published)
        return { cache, cached: true }
      } catch {
        // Cache persistence must never make an otherwise valid local preview unusable.
      }
    }
    return { cache, cached: false }
  }

  async function prepareBuildImage() {
    if (!build.value) return
    printStatus.value = ''
    printBusy.value = true
    try {
      await ensurePrintPreview()
      printStatus.value = t('builds.print.previewReady')
    } catch {
      printStatus.value = t('builds.print.error')
    } finally {
      printBusy.value = false
    }
  }

  async function downloadBuildImagePng() {
    if (!build.value) return
    printStatus.value = ''
    printBusy.value = true
    try {
      if (!printPreviewUrl.value) await ensurePrintPreview()
      if (printPreviewBlob) downloadBuildPrintPngBlob(build.value, printPreviewBlob)
      else await downloadBuildPrintPngFromUrl(build.value, printPreviewUrl.value)
      printStatus.value = t('builds.print.downloadedPng')
    } catch {
      printStatus.value = t('builds.print.error')
    } finally {
      printBusy.value = false
    }
  }

  async function downloadBuildImageSvg() {
    if (!build.value) return
    printStatus.value = ''
    try {
      await downloadBuildPrintSvg(build.value, { t, optionLabel, optionImage })
      printStatus.value = t('builds.print.downloadedSvg')
    } catch {
      printStatus.value = t('builds.print.error')
    }
  }

  async function printBuildSheet() {
    if (!build.value) return
    printStatus.value = ''
    try {
      await openBuildPrintWindow(build.value, { t, optionLabel, optionImage })
      printStatus.value = t('builds.print.windowOpened')
    } catch {
      printStatus.value = t('builds.print.error')
    }
  }

  async function publishBuildImage(notifyDiscord = false) {
    if (!build.value) return
    printStatus.value = ''
    printBusy.value = true
    try {
      const current = await refreshBuildForCache()
      const cache = await createBuildPrintCacheDescriptor(current, { t, optionLabel, optionImage })
      if (!notifyDiscord && cacheMatches(current, cache)) {
        await navigator.clipboard.writeText(absoluteFileUrl(current.printout_url) || current.printout_url)
        printStatus.value = t('builds.print.publicLinkCopied')
        return
      }
      const image = await createBuildPrintPngBlob(current, { t, optionLabel, optionImage })
      const published = await publishBuildPrintout(current.id, image, notifyDiscord, cache)
      applyPublishedCache(published)
      if (notifyDiscord) {
        printStatus.value = t('builds.print.discordQueued')
      } else {
        await navigator.clipboard.writeText(absoluteFileUrl(published.url) || published.url)
        printStatus.value = published.changed
          ? t('builds.print.publicLinkPublished')
          : t('builds.print.publicLinkCopied')
      }
    } catch {
      printStatus.value = t('builds.print.publishError')
    } finally {
      printBusy.value = false
    }
  }

  function closePrintPreview() {
    printPreviewOpen.value = false
    revokePrintPreview()
  }

  onBeforeUnmount(revokePrintPreview)

  return {
    printStatus,
    printPreviewUrl,
    printPreviewOpen,
    printBusy,
    revokePrintPreview,
    ensurePrintPreview,
    prepareBuildImage,
    downloadBuildImagePng,
    downloadBuildImageSvg,
    printBuildSheet,
    publishBuildImage,
    closePrintPreview,
  }
}
