import { onBeforeUnmount, ref } from 'vue'
import {
  createBuildPrintPreviewUrl,
  downloadBuildPrintPng,
  downloadBuildPrintSvg,
  openBuildPrintWindow,
} from '@/modules/builds/buildPrintExport'

export function useBuildPrintActions(build, { optionImage, optionLabel, t }) {
  const printStatus = ref('')
  const printPreviewUrl = ref('')
  const printPreviewOpen = ref(false)
  const printBusy = ref(false)

  function revokePrintPreview() {
    if (printPreviewUrl.value) URL.revokeObjectURL(printPreviewUrl.value)
    printPreviewUrl.value = ''
  }

  function ensurePrintPreview() {
    revokePrintPreview()
    printPreviewUrl.value = createBuildPrintPreviewUrl(build.value, { t, optionLabel, optionImage })
    printPreviewOpen.value = true
  }

  async function prepareBuildImage() {
    if (!build.value) return
    printStatus.value = ''
    printBusy.value = true
    try {
      ensurePrintPreview()
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
      if (!printPreviewUrl.value) ensurePrintPreview()
      await downloadBuildPrintPng(build.value, { t, optionLabel, optionImage })
      printStatus.value = t('builds.print.downloadedPng')
    } catch {
      printStatus.value = t('builds.print.error')
    } finally {
      printBusy.value = false
    }
  }

  function downloadBuildImageSvg() {
    if (!build.value) return
    printStatus.value = ''
    try {
      if (!printPreviewUrl.value) ensurePrintPreview()
      downloadBuildPrintSvg(build.value, { t, optionLabel, optionImage })
      printStatus.value = t('builds.print.downloadedSvg')
    } catch {
      printStatus.value = t('builds.print.error')
    }
  }

  function printBuildSheet() {
    if (!build.value) return
    printStatus.value = ''
    try {
      openBuildPrintWindow(build.value, { t, optionLabel, optionImage })
      printStatus.value = t('builds.print.windowOpened')
    } catch {
      printStatus.value = t('builds.print.error')
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
    closePrintPreview,
  }
}
