import assert from 'node:assert/strict'
import test from 'node:test'

import {
  createPrintDocumentHtml,
  escapePrintMarkup,
  resolvePrintUrl,
  sanitizePrintFileName,
} from '../src/shared/printing/printDocument.js'

test('shared print shell provides one accessible and persistent theme toolbar', () => {
  const html = createPrintDocumentHtml({
    lang: 'de',
    title: 'Fleet <Report>',
    body: '<main>Document</main>',
    labels: {
      themeLabel: 'Darstellung',
      themeSystem: 'Automatisch',
      themeLight: 'Hell',
      themeDark: 'Dunkel',
      printAction: 'Als PDF speichern',
    },
  })

  assert.match(html, /<html lang="de">/)
  assert.match(html, /Fleet &lt;Report&gt;/)
  assert.equal((html.match(/class="print-toolbar"/g) || []).length, 1)
  assert.match(html, /aria-pressed="true"/)
  assert.match(html, /rbf-print-theme/)
  assert.match(html, /prefers-color-scheme:dark/)
  assert.match(html, /Als PDF speichern/)
})

test('shared print formatting helpers normalize markup, URLs and filenames', () => {
  assert.equal(escapePrintMarkup('<fleet & crew>'), '&lt;fleet &amp; crew&gt;')
  assert.equal(resolvePrintUrl('/guides/7', { origin: 'https://fleet.example' }), 'https://fleet.example/guides/7')
  assert.equal(sanitizePrintFileName('Santisima Trinidad #1', 'fleet'), 'santisima-trinidad-1')
})
