const PRINT_THEME_STORAGE_KEY = 'rbf-print-theme'
const LEGACY_PRINT_THEME_STORAGE_KEY = 'rbf-guide-print-theme'
const PRINT_THEMES = Object.freeze(['system', 'light', 'dark'])

function escapePrintMarkup(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function resolvePrintUrl(value, locationObject) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (/^https?:\/\//i.test(raw)) return raw
  const origin = locationObject?.origin || (typeof window !== 'undefined' ? window.location.origin : '')
  if (!origin) return raw
  try {
    return new URL(raw, origin).href
  } catch {
    return raw
  }
}

function sanitizePrintFileName(value, fallback = 'document') {
  return String(value || fallback)
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[^a-z0-9]+/g, '-')  // Check if sanitization is good enough to prevent malicious files
    .replace(/(^-|-$)/g, '')
    .slice(0, 72) || fallback
}

function triggerPrintDownload(blob, fileName) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1500)
}

function createPrintLabels(t) {
  return {
    themeLabel: t('print.themeLabel'),
    themeSystem: t('print.themeSystem'),
    themeLight: t('print.themeLight'),
    themeDark: t('print.themeDark'),
    printAction: t('print.action'),
  }
}

function createPrintDocumentHtml({
  lang = 'en',
  title = 'Royal Blackwater Fleet',
  body = '',
  styles = '',
  labels = {},
  storageKey = PRINT_THEME_STORAGE_KEY,
  extraScript = '',
} = {}) {
  const normalizedLabels = {
    themeLabel: labels.themeLabel || 'Appearance',
    themeSystem: labels.themeSystem || 'System',
    themeLight: labels.themeLight || 'Light',
    themeDark: labels.themeDark || 'Dark',
    printAction: labels.printAction || 'Print or save as PDF',
  }
  const serializedStorageKey = JSON.stringify(String(storageKey || PRINT_THEME_STORAGE_KEY))
  const serializedLegacyStorageKey = JSON.stringify(LEGACY_PRINT_THEME_STORAGE_KEY)

  return `<!doctype html>
<html lang="${escapePrintMarkup(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${escapePrintMarkup(title)}</title>
  <style>
    :root{color-scheme:light;--navy:#071d3d;--navy-soft:#17365d;--gold:#a87516;--ink:#17202b;--muted:#566271;--rule:#ccd3dc;--border:#aeb8c4;--paper:#fff;--canvas:#e9edf1;--surface:#fff;--surface-soft:#fafbfc;--callout:#fbf8f0;--code:#f4f6f8;--link:#174b91;--toolbar:rgba(255,255,255,.95);--button-text:#fff;--document-shadow:rgba(7,29,61,.18)}
    html[data-theme="dark"]{color-scheme:dark;--navy:#f1c979;--navy-soft:#8ca9c5;--gold:#e4b457;--ink:#eef4fa;--muted:#a7b5c3;--rule:#33485c;--border:#465c70;--paper:#081522;--canvas:#02080e;--surface:#0d1e2c;--surface-soft:#0c1a26;--callout:#132333;--code:#06111b;--link:#8fc1ff;--toolbar:rgba(8,21,34,.96);--button-text:#07111a;--document-shadow:rgba(0,0,0,.55)}
    @media(prefers-color-scheme:dark){html:not([data-theme]){color-scheme:dark;--navy:#f1c979;--navy-soft:#8ca9c5;--gold:#e4b457;--ink:#eef4fa;--muted:#a7b5c3;--rule:#33485c;--border:#465c70;--paper:#081522;--canvas:#02080e;--surface:#0d1e2c;--surface-soft:#0c1a26;--callout:#132333;--code:#06111b;--link:#8fc1ff;--toolbar:rgba(8,21,34,.96);--button-text:#07111a;--document-shadow:rgba(0,0,0,.55)}}
    *{box-sizing:border-box}
    html,body{min-height:100%;background:var(--canvas)}
    body{margin:0;color:var(--ink);font-family:Inter,"Segoe UI",Arial,sans-serif}
    .print-toolbar{position:fixed;z-index:10;top:1rem;right:1rem;display:flex;align-items:center;gap:.6rem;padding:.55rem;border:1px solid var(--rule);border-radius:.4rem;background:var(--toolbar);box-shadow:0 .8rem 2rem var(--document-shadow);backdrop-filter:blur(14px)}
    .print-toolbar button{min-height:2.4rem;padding:.55rem 1rem;border:1px solid var(--navy);border-radius:.22rem;background:var(--navy);color:var(--button-text);font:700 .84rem/1 Inter,"Segoe UI",sans-serif;cursor:pointer}
    .print-theme{display:flex;align-items:center;gap:.28rem;padding-right:.6rem;border-right:1px solid var(--rule)}
    .print-theme>span{margin-right:.2rem;color:var(--muted);font-size:.72rem;font-weight:750;text-transform:uppercase;letter-spacing:.08em}
    .print-theme button{min-height:2rem;padding:.42rem .62rem;border-color:transparent;background:transparent;color:var(--muted);font-size:.74rem}
    html:not([data-theme]) [data-theme-choice="system"],html[data-theme="light"] [data-theme-choice="light"],html[data-theme="dark"] [data-theme-choice="dark"]{border-color:var(--gold);background:var(--surface-soft);color:var(--navy)}
    @media print{html,body{background:var(--paper);-webkit-print-color-adjust:exact;print-color-adjust:exact}.print-toolbar{display:none!important}}
    @media screen and (max-width:760px){.print-toolbar{left:.5rem;right:.5rem;flex-wrap:wrap;justify-content:space-between}.print-theme{flex:1 1 100%;justify-content:center;padding:0 0 .45rem;border-right:0;border-bottom:1px solid var(--rule)}}
    ${styles}
  </style>
</head>
<body>
  <div class="print-toolbar" role="toolbar" aria-label="${escapePrintMarkup(normalizedLabels.themeLabel)}">
    <div class="print-theme">
      <span>${escapePrintMarkup(normalizedLabels.themeLabel)}</span>
      <button type="button" data-theme-choice="system" aria-pressed="true" onclick="setRbfPrintTheme('system')">${escapePrintMarkup(normalizedLabels.themeSystem)}</button>
      <button type="button" data-theme-choice="light" aria-pressed="false" onclick="setRbfPrintTheme('light')">${escapePrintMarkup(normalizedLabels.themeLight)}</button>
      <button type="button" data-theme-choice="dark" aria-pressed="false" onclick="setRbfPrintTheme('dark')">${escapePrintMarkup(normalizedLabels.themeDark)}</button>
    </div>
    <button type="button" data-print-action onclick="window.print()">${escapePrintMarkup(normalizedLabels.printAction)}</button>
  </div>
  ${body}
  <script>
    const rbfPrintThemeStorageKey=${serializedStorageKey}
    const rbfLegacyPrintThemeStorageKey=${serializedLegacyStorageKey}
    const rbfPrintThemeMedia=window.matchMedia('(prefers-color-scheme: dark)')
    function resolveRbfPrintTheme(theme){return theme==='system'?(rbfPrintThemeMedia.matches?'dark':'light'):theme}
    function updateRbfPrintThemeButtons(theme){
      document.querySelectorAll('[data-theme-choice]').forEach((button)=>button.setAttribute('aria-pressed',String(button.dataset.themeChoice===theme)))
    }
    function notifyRbfPrintTheme(theme){window.dispatchEvent(new CustomEvent('rbf-print-theme-change',{detail:{theme,resolvedTheme:resolveRbfPrintTheme(theme)}}))}
    function setRbfPrintTheme(theme){
      if(theme==='system') document.documentElement.removeAttribute('data-theme')
      else document.documentElement.setAttribute('data-theme',theme)
      updateRbfPrintThemeButtons(theme)
      try{localStorage.setItem(rbfPrintThemeStorageKey,theme)}catch{}
      notifyRbfPrintTheme(theme)
    }
    let savedRbfPrintTheme='system'
    try{savedRbfPrintTheme=localStorage.getItem(rbfPrintThemeStorageKey)||localStorage.getItem(rbfLegacyPrintThemeStorageKey)||'system'}catch{}
    if(!${JSON.stringify(PRINT_THEMES)}.includes(savedRbfPrintTheme)) savedRbfPrintTheme='system'
    setRbfPrintTheme(savedRbfPrintTheme)
    rbfPrintThemeMedia.addEventListener?.('change',()=>{if(!document.documentElement.hasAttribute('data-theme')) notifyRbfPrintTheme('system')})
    ${extraScript}
  </script>
</body>
</html>`
}

function openPrintWindow(html, { features = '', errorMessage = 'Print view could not be opened.' } = {}) {
  const popup = window.open('', '_blank', features)
  if (!popup) throw new Error(errorMessage)
  popup.opener = null
  popup.document.open()
  popup.document.write(html)
  popup.document.close()
  popup.focus()
  return popup
}

export {
  PRINT_THEME_STORAGE_KEY,
  createPrintDocumentHtml,
  createPrintLabels,
  escapePrintMarkup,
  openPrintWindow,
  resolvePrintUrl,
  sanitizePrintFileName,
  triggerPrintDownload,
}
