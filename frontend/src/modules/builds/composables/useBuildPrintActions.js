import { onBeforeUnmount, ref } from 'vue'
import {
  createBuildPrintPngBlob,
  createBuildPrintPreviewUrl,
  downloadBuildPrintPng,
  downloadBuildPrintSvg,
  openBuildPrintWindow,
} from '@/modules/builds/buildPrintExport'
import { publishBuildPrintout } from '@/modules/builds/api/builds'
import { absoluteFileUrl } from '@/modules/files/api/files'

export function useBuildPrintActions(build, { optionImage, optionLabel, t }) {
  const printStatus = ref('')
  const printPreviewUrl = ref('')
  const printPreviewOpen = ref(false)
  const printBusy = ref(false)

  function revokePrintPreview() {
    if (printPreviewUrl.value) URL.revokeObjectURL(printPreviewUrl.value)
    printPreviewUrl.value = ''
  }

  async function ensurePrintPreview() {
    revokePrintPreview()
    printPreviewUrl.value = await createBuildPrintPreviewUrl(build.value, { t, optionLabel, optionImage })
    printPreviewOpen.value = true
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
      await downloadBuildPrintPng(build.value, { t, optionLabel, optionImage })
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
      if (!printPreviewUrl.value) await ensurePrintPreview()
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
      const image = await createBuildPrintPngBlob(build.value, { t, optionLabel, optionImage })
      const published = await publishBuildPrintout(build.value.id, image, notifyDiscord)
      build.value.printout_url = published.url
      build.value.printout_checksum = published.checksum
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
