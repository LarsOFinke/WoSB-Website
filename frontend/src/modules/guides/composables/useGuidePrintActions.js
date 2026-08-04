import { ref } from 'vue'

import { openGuidePrintWindow } from '@/modules/guides/guidePrintExport'
import { renderMarkdown } from '@/shared/content/markdown'

export function useGuidePrintActions(guide, { t }) {
  const printBusy = ref(false)
  const printStatus = ref('')

  function printGuide() {
    if (!guide.value) return
    printBusy.value = true
    printStatus.value = ''
    try {
      openGuidePrintWindow(guide.value, { t, renderMarkdown })
      printStatus.value = t('guides.print.windowOpened')
    } catch {
      printStatus.value = t('guides.print.error')
    } finally {
      printBusy.value = false
    }
  }

  return { printBusy, printStatus, printGuide }
}
