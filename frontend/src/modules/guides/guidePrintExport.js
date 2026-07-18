import { renderMarkdown as renderSafeMarkdown } from '../../shared/content/markdown.js'
import {
  parseRichTextEmbeds,
  unembeddedAttachments,
  unembeddedBuilds,
} from '../../shared/content/richTextEmbeds.js'

const PRINT_BRAND = 'Royal Blackwater Fleet'

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function stripInlineMarkdown(value) {
  return String(value || '')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_~`>#]/g, '')
    .trim()
}

function extractGuideHeadings(body) {
  return String(body || '')
    .split(/\r?\n/)
    .map((line) => line.match(/^\s*(#{1,3})\s+(.+?)\s*#*\s*$/))
    .filter(Boolean)
    .map((match, index) => ({
      level: match[1].length,
      label: stripInlineMarkdown(match[2]),
      number: String(index + 1).padStart(2, '0'),
    }))
    .filter((heading) => heading.label)
}

function formatFileSize(sizeBytes) {
  const size = Number(sizeBytes || 0)
  if (!Number.isFinite(size) || size <= 0) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  const rounded = value >= 10 || unitIndex === 0 ? Math.round(value) : value.toFixed(1)
  return `${rounded} ${units[unitIndex]}`
}

function fileKind(file) {
  const mimeType = String(file?.mime_type || '').toLowerCase()
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('video/')) return 'video'
  if (mimeType === 'application/pdf') return 'pdf'
  if (mimeType === 'text/plain') return 'text'
  return 'file'
}

function resolveUrl(value, locationObject) {
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

function defaultFormatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function createFileModel(file, helpers) {
  return {
    id: Number(file?.id || 0),
    name: file?.original_name || helpers.t('guides.print.attachmentFallback'),
    kind: fileKind(file),
    kindLabel: helpers.t(`files.kind.${fileKind(file)}`),
    sizeLabel: formatFileSize(file?.size_bytes),
    url: resolveUrl(file?.public_url, helpers.locationObject),
  }
}

function createBuildModel(build, helpers) {
  const stats = build?.ship_stats || {}
  const ship = build?.ship || {}
  return {
    id: Number(build?.id || 0),
    name: build?.build_name || helpers.t('builds.print.fallbackTitle'),
    shipName: ship.name || '—',
    meta: [
      ship.rate ? `${helpers.t('common.rate')} ${ship.rate}` : '',
      helpers.t(`builds.types.${build?.build_type || 'balanced'}`),
    ].filter(Boolean).join(' · '),
    crew: helpers.t('builds.list.crew', {
      current: Number(stats.crew_total || 0),
      max: Number(stats.crew_capacity || ship.crew_capacity || 0),
    }),
    upgrades: helpers.t('builds.list.upgradeSummary', {
      used: Number(stats.upgrade_slots_used || 0),
      max: Number(stats.upgrade_slots_available || 0),
    }),
    url: resolveUrl(`/builds/${build?.id}`, helpers.locationObject),
  }
}

function createGuidePrintModel(guide, options = {}) {
  const t = options.t || ((key) => key)
  const helpers = {
    t,
    locationObject: options.locationObject || (typeof window !== 'undefined' ? window.location : null),
  }
  const formatDate = options.formatDate || defaultFormatDate
  const attachmentMap = new Map((guide?.attachments || []).map((file) => [Number(file.id), file]))
  const buildMap = new Map((guide?.builds || []).map((build) => [Number(build.id), build]))
  const parts = parseRichTextEmbeds(guide?.body || '').map((part) => {
    if (part.type === 'fileEmbed') {
      const file = attachmentMap.get(Number(part.fileId))
      return file
        ? { ...part, type: 'file', file: createFileModel(file, helpers) }
        : { ...part, type: 'missingFile' }
    }
    if (part.type === 'buildEmbed') {
      const build = buildMap.get(Number(part.buildId))
      return build
        ? { ...part, type: 'build', build: createBuildModel(build, helpers) }
        : { ...part, type: 'missingBuild' }
    }
    return part
  })

  return {
    id: Number(guide?.id || 0),
    title: guide?.title || t('guides.print.fallbackTitle'),
    category: t(`guides.categories.${guide?.category || 'general'}`),
    summary: String(guide?.summary || '').trim(),
    author: guide?.owner?.display_name || t('guides.print.unknownAuthor'),
    createdAt: formatDate(guide?.created_at),
    updatedAt: formatDate(guide?.updated_at),
    preparedAt: formatDate(new Date()),
    sourceUrl: resolveUrl(`/guides/${guide?.id}`, helpers.locationObject),
    tableOfContents: extractGuideHeadings(guide?.body),
    parts,
    attachments: unembeddedAttachments(guide?.attachments || [], guide?.body)
      .map((file) => createFileModel(file, helpers)),
    builds: unembeddedBuilds(guide?.builds || [], guide?.body)
      .map((build) => createBuildModel(build, helpers)),
  }
}

function renderFile(file) {
  const meta = [file.kindLabel, file.sizeLabel].filter(Boolean).join(' · ')
  if (file.kind === 'image' && file.url) {
    return `<figure class="guide-print-media"><img src="${escapeHtml(file.url)}" alt="${escapeHtml(file.name)}"><figcaption><strong>${escapeHtml(file.name)}</strong>${meta ? ` · ${escapeHtml(meta)}` : ''}</figcaption></figure>`
  }
  return `<article class="guide-print-resource"><div><strong>${escapeHtml(file.name)}</strong><span>${escapeHtml(meta)}</span></div>${file.url ? `<a href="${escapeHtml(file.url)}">${escapeHtml(file.url)}</a>` : ''}</article>`
}

function renderBuild(build, t) {
  return `<article class="guide-print-build"><div class="guide-print-build-main"><span>${escapeHtml(t('guides.print.linkedBuildEyebrow'))}</span><strong>${escapeHtml(build.name)}</strong><small>${escapeHtml(build.shipName)} · ${escapeHtml(build.meta)}</small></div><div class="guide-print-build-stats"><span>${escapeHtml(build.crew)}</span><span>${escapeHtml(build.upgrades)}</span></div>${build.url ? `<a href="${escapeHtml(build.url)}">${escapeHtml(build.url)}</a>` : ''}</article>`
}

function renderGuideParts(model, helpers) {
  const renderMarkdown = helpers.renderMarkdown || renderSafeMarkdown
  return model.parts.map((part) => {
    if (part.type === 'text') return `<div class="guide-print-copy">${renderMarkdown(part.text)}</div>`
    if (part.type === 'file') return renderFile(part.file)
    if (part.type === 'build') return renderBuild(part.build, model.t || helpers.t)
    if (part.type === 'missingFile') return `<p class="guide-print-missing">${escapeHtml(helpers.t('files.inlineMissing', { id: part.fileId }))}</p>`
    if (part.type === 'missingBuild') return `<p class="guide-print-missing">${escapeHtml(helpers.t('buildEmbeds.inlineMissing', { id: part.buildId }))}</p>`
    return ''
  }).join('')
}

function renderContents(model, t) {
  if (!model.tableOfContents.length) return ''
  return `<aside class="guide-print-contents"><h2>${escapeHtml(t('guides.print.contentsTitle'))}</h2><ol>${model.tableOfContents.map((heading) => `<li class="level-${heading.level}"><span>${escapeHtml(heading.number)}</span>${escapeHtml(heading.label)}</li>`).join('')}</ol></aside>`
}

function renderReferenceSections(model, t) {
  const builds = model.builds.length
    ? `<section class="guide-print-references"><h2>${escapeHtml(t('guides.print.linkedBuildsTitle'))}</h2>${model.builds.map((build) => renderBuild(build, t)).join('')}</section>`
    : ''
  const attachments = model.attachments.length
    ? `<section class="guide-print-references"><h2>${escapeHtml(t('guides.print.attachmentsTitle'))}</h2>${model.attachments.map(renderFile).join('')}</section>`
    : ''
  return `${builds}${attachments}`
}

function createGuidePrintHtml(guide, options = {}) {
  const t = options.t || ((key) => key)
  const model = createGuidePrintModel(guide, options)
  model.t = t
  const lang = escapeHtml(options.lang || (typeof document !== 'undefined' ? document.documentElement.lang : 'en') || 'en')
  const title = escapeHtml(model.title)
  const body = renderGuideParts(model, { ...options, t })
  const referenceSections = renderReferenceSections(model, t)
  const mastheadLogo = resolveUrl('/rbf-fleet-icon.png', options.locationObject || (typeof window !== 'undefined' ? window.location : null))

  return `<!doctype html>
<html lang="${lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${title} · ${PRINT_BRAND}</title>
  <style>
    :root{color-scheme:light;--navy:#071d3d;--navy-soft:#17365d;--gold:#a87516;--ink:#17202b;--muted:#566271;--rule:#ccd3dc;--border:#aeb8c4;--paper:#fff;--canvas:#e9edf1;--surface:#fff;--surface-soft:#fafbfc;--callout:#fbf8f0;--code:#f4f6f8;--link:#174b91;--toolbar:rgba(255,255,255,.95);--button-text:#fff;--document-shadow:rgba(7,29,61,.18)}
    html[data-theme="dark"]{color-scheme:dark;--navy:#f1c979;--navy-soft:#8ca9c5;--gold:#e4b457;--ink:#eef4fa;--muted:#a7b5c3;--rule:#33485c;--border:#465c70;--paper:#081522;--canvas:#02080e;--surface:#0d1e2c;--surface-soft:#0c1a26;--callout:#132333;--code:#06111b;--link:#8fc1ff;--toolbar:rgba(8,21,34,.96);--button-text:#07111a;--document-shadow:rgba(0,0,0,.55)}
    @media(prefers-color-scheme:dark){html:not([data-theme]){color-scheme:dark;--navy:#f1c979;--navy-soft:#8ca9c5;--gold:#e4b457;--ink:#eef4fa;--muted:#a7b5c3;--rule:#33485c;--border:#465c70;--paper:#081522;--canvas:#02080e;--surface:#0d1e2c;--surface-soft:#0c1a26;--callout:#132333;--code:#06111b;--link:#8fc1ff;--toolbar:rgba(8,21,34,.96);--button-text:#07111a;--document-shadow:rgba(0,0,0,.55)}}
    *{box-sizing:border-box}
    html{background:var(--canvas)}
    body{margin:0;background:var(--canvas);color:var(--ink);font-family:Inter,"Segoe UI",Arial,sans-serif;font-size:10.5pt;line-height:1.58}
    a{color:var(--link);text-decoration-thickness:.06em;text-underline-offset:.13em;overflow-wrap:anywhere}
    .guide-print-toolbar{position:fixed;z-index:5;top:1rem;right:1rem;display:flex;align-items:center;gap:.6rem;padding:.55rem;border:1px solid var(--rule);border-radius:.4rem;background:var(--toolbar);box-shadow:0 .8rem 2rem var(--document-shadow);backdrop-filter:blur(14px)}
    .guide-print-toolbar button{min-height:2.4rem;padding:.55rem 1rem;border:1px solid var(--navy);border-radius:.22rem;background:var(--navy);color:var(--button-text);font:700 .84rem/1 Inter,"Segoe UI",sans-serif;cursor:pointer}
    .guide-print-theme{display:flex;align-items:center;gap:.28rem;padding-right:.6rem;border-right:1px solid var(--rule)}
    .guide-print-theme>span{margin-right:.2rem;color:var(--muted);font-size:.72rem;font-weight:750;text-transform:uppercase;letter-spacing:.08em}
    .guide-print-theme button{min-height:2rem;padding:.42rem .62rem;border-color:transparent;background:transparent;color:var(--muted);font-size:.74rem}
    html:not([data-theme]) [data-theme-choice="system"],html[data-theme="light"] [data-theme-choice="light"],html[data-theme="dark"] [data-theme-choice="dark"]{border-color:var(--gold);background:var(--surface-soft);color:var(--navy)}
    .guide-print-document{width:210mm;min-height:297mm;margin:5.2rem auto 1.4rem;padding:15mm 16mm 18mm;background:var(--paper);box-shadow:0 1rem 3.5rem var(--document-shadow)}
    .guide-print-masthead{display:flex;align-items:center;gap:4mm;padding-bottom:4mm;border-bottom:1.2pt solid var(--navy)}
    .guide-print-masthead img{width:13mm;height:13mm;object-fit:contain}
    .guide-print-brand{display:grid;gap:.7mm;color:var(--navy)}
    .guide-print-brand strong{font-family:Georgia,"Times New Roman",serif;font-size:17pt;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
    .guide-print-brand span{color:var(--gold);font-size:7.5pt;font-weight:750;letter-spacing:.18em;text-transform:uppercase}
    .guide-print-cover{padding:7mm 0 6mm;border-bottom:.8pt solid var(--gold)}
    .guide-print-cover h1{max-width:165mm;margin:0;color:var(--navy);font-family:Georgia,"Times New Roman",serif;font-size:28pt;line-height:1.05;letter-spacing:-.025em;overflow-wrap:anywhere}
    .guide-print-category{display:block;margin-top:3.5mm;color:var(--gold);font-size:9pt;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
    .guide-print-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2mm 8mm;margin:5mm 0 0;padding:0;list-style:none;color:var(--muted);font-size:8.5pt}
    .guide-print-meta li{display:grid;grid-template-columns:16mm minmax(0,1fr);gap:2mm}
    .guide-print-meta strong{color:var(--navy);font-weight:750}
    .guide-print-meta .source{grid-column:1/-1}
    .guide-print-intro{display:grid;grid-template-columns:minmax(0,1fr) 54mm;gap:9mm;align-items:start;padding:6mm 0 4mm}
    .guide-print-summary{margin:0;color:var(--ink);font-size:11pt;line-height:1.65}
    .guide-print-contents{padding-left:6mm;border-left:1pt solid var(--navy-soft)}
    .guide-print-contents h2{margin:0 0 2mm;color:var(--navy);font-family:Georgia,"Times New Roman",serif;font-size:11pt;text-transform:uppercase;letter-spacing:.06em}
    .guide-print-contents ol{display:grid;gap:1.25mm;margin:0;padding:0;list-style:none;font-size:8.5pt}
    .guide-print-contents li{display:grid;grid-template-columns:8mm 1fr;gap:1mm;color:var(--ink)}
    .guide-print-contents li.level-3{padding-left:4mm;color:var(--muted)}
    .guide-print-body{counter-reset:guide-section;min-width:0}
    .guide-print-copy{min-width:0}
    .guide-print-copy:empty{display:none}
    .guide-print-copy h1,.guide-print-copy h2{counter-increment:guide-section;display:flex;align-items:baseline;gap:4mm;margin:8mm 0 3mm;padding-bottom:1.5mm;border-bottom:.8pt solid var(--gold);color:var(--navy);font-family:Georgia,"Times New Roman",serif;font-size:17pt;line-height:1.15;break-after:avoid-page}
    .guide-print-copy h1::before,.guide-print-copy h2::before{content:counter(guide-section,decimal-leading-zero);font-size:14pt;letter-spacing:.08em}
    .guide-print-copy h3{margin:5mm 0 2mm;color:var(--navy);font-family:Georgia,"Times New Roman",serif;font-size:12.5pt;break-after:avoid-page}
    .guide-print-copy p{margin:0 0 3.2mm;orphans:3;widows:3}
    .guide-print-copy ul,.guide-print-copy ol{margin:1.5mm 0 4mm;padding-left:7mm}
    .guide-print-copy li{margin:1.25mm 0;padding-left:1mm;break-inside:avoid-page}
    .guide-print-copy blockquote{margin:4mm 0;padding:3.5mm 4mm;border:.8pt solid var(--gold);border-left:3pt solid var(--gold);background:var(--callout);color:var(--ink);font-family:Georgia,"Times New Roman",serif;font-style:italic;break-inside:avoid-page}
    .guide-print-copy blockquote p:last-child{margin-bottom:0}
    .guide-print-copy pre{max-width:100%;margin:4mm 0;padding:4mm;border:.8pt solid var(--rule);background:var(--code);color:var(--ink);font:8.5pt/1.5 "SFMono-Regular",Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid-page}
    .guide-print-copy code{font-family:"SFMono-Regular",Consolas,monospace;font-size:.9em}
    .guide-print-copy table{width:100%;margin:4mm 0;border-collapse:collapse;font-size:8.5pt;break-inside:avoid-page}
    .guide-print-copy th,.guide-print-copy td{padding:2mm;border:.6pt solid var(--border);text-align:left;vertical-align:top}
    .guide-print-copy th{background:var(--surface);color:var(--navy)}
    .guide-print-media{margin:5mm 0;break-inside:avoid-page}
    .guide-print-media img{display:block;width:100%;max-height:112mm;border:.8pt solid var(--border);object-fit:contain}
    .guide-print-media figcaption{margin-top:1.5mm;color:var(--muted);font-size:8pt;font-style:italic}
    .guide-print-build,.guide-print-resource{display:grid;gap:2mm;margin:3mm 0;padding:3.5mm 4mm;border:.8pt solid var(--border);border-left:2.4pt solid var(--gold);background:var(--surface-soft);break-inside:avoid-page}
    .guide-print-build{grid-template-columns:minmax(0,1fr) auto;align-items:center}
    .guide-print-build-main{display:grid;gap:.6mm}
    .guide-print-build-main>span{color:var(--gold);font-size:7pt;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
    .guide-print-build-main>strong{color:var(--navy);font-size:10.5pt}
    .guide-print-build-main small{color:var(--muted);font-size:8pt}
    .guide-print-build-stats{display:grid;gap:.8mm;text-align:right;color:var(--muted);font-size:8pt}
    .guide-print-build>a{grid-column:1/-1;font-size:7.5pt}
    .guide-print-resource{grid-template-columns:48mm minmax(0,1fr);align-items:start;font-size:8pt}
    .guide-print-resource>div{display:grid;gap:.6mm}
    .guide-print-resource span{color:var(--muted)}
    .guide-print-missing{padding:3mm;border:.8pt dashed #b7c0ca;color:var(--muted);font-size:8.5pt;break-inside:avoid-page}
    .guide-print-references{margin-top:8mm;break-before:auto}
    .guide-print-references>h2{margin:0 0 3mm;padding-bottom:1.5mm;border-bottom:.8pt solid var(--gold);color:var(--navy);font-family:Georgia,"Times New Roman",serif;font-size:15pt;break-after:avoid-page}
    .guide-print-footer{display:flex;justify-content:space-between;gap:8mm;margin-top:10mm;padding-top:3mm;border-top:.8pt solid var(--navy);color:var(--muted);font-size:7.5pt;break-inside:avoid-page}
    .guide-print-footer strong{color:var(--navy)}
    @page{size:A4 portrait;margin:15mm 16mm 18mm}
    @media print{
      html,body{background:var(--paper);-webkit-print-color-adjust:exact;print-color-adjust:exact}
      body{font-size:10.5pt}
      .guide-print-toolbar{display:none!important}
      .guide-print-document{width:auto;min-height:0;margin:0;padding:0;box-shadow:none}
      a{color:var(--link)}
      .guide-print-masthead{break-after:avoid-page}
      .guide-print-cover,.guide-print-intro{break-inside:avoid-page}
      .guide-print-footer{position:relative}
    }
    @media screen and (max-width:760px){
      .guide-print-document{width:calc(100% - 1rem);min-height:0;margin:7.8rem .5rem 1rem;padding:1.1rem}
      .guide-print-toolbar{left:.5rem;right:.5rem;flex-wrap:wrap;justify-content:space-between}
      .guide-print-theme{flex:1 1 100%;justify-content:center;padding:0 0 .45rem;border-right:0;border-bottom:1px solid var(--rule)}
      .guide-print-intro{grid-template-columns:1fr}
      .guide-print-meta{grid-template-columns:1fr}
      .guide-print-meta .source{grid-column:auto}
      .guide-print-build{grid-template-columns:1fr}
      .guide-print-build-stats{text-align:left}
      .guide-print-resource{grid-template-columns:1fr}
    }
  </style>
</head>
<body>
  <div class="guide-print-toolbar" role="toolbar" aria-label="${escapeHtml(t('guides.print.themeLabel'))}">
    <div class="guide-print-theme">
      <span>${escapeHtml(t('guides.print.themeLabel'))}</span>
      <button type="button" data-theme-choice="system" aria-pressed="true" onclick="setGuidePrintTheme('system')">${escapeHtml(t('guides.print.themeSystem'))}</button>
      <button type="button" data-theme-choice="light" aria-pressed="false" onclick="setGuidePrintTheme('light')">${escapeHtml(t('guides.print.themeLight'))}</button>
      <button type="button" data-theme-choice="dark" aria-pressed="false" onclick="setGuidePrintTheme('dark')">${escapeHtml(t('guides.print.themeDark'))}</button>
    </div>
    <button type="button" onclick="window.print()">${escapeHtml(t('guides.print.printAction'))}</button>
  </div>
  <main class="guide-print-document">
    <header class="guide-print-masthead">
      ${mastheadLogo ? `<img src="${escapeHtml(mastheadLogo)}" alt="">` : ''}
      <div class="guide-print-brand"><strong>${PRINT_BRAND}</strong><span>${escapeHtml(t('guides.print.brandMotto'))}</span></div>
    </header>
    <section class="guide-print-cover">
      <h1>${title}</h1>
      <span class="guide-print-category">${escapeHtml(model.category)}</span>
      <ul class="guide-print-meta">
        <li><strong>${escapeHtml(t('guides.print.author'))}</strong><span>${escapeHtml(model.author)}</span></li>
        <li><strong>${escapeHtml(t('guides.print.updated'))}</strong><span>${escapeHtml(model.updatedAt || model.createdAt)}</span></li>
        <li class="source"><strong>${escapeHtml(t('guides.print.source'))}</strong><a href="${escapeHtml(model.sourceUrl)}">${escapeHtml(model.sourceUrl)}</a></li>
      </ul>
    </section>
    ${(model.summary || model.tableOfContents.length) ? `<section class="guide-print-intro">${model.summary ? `<p class="guide-print-summary">${escapeHtml(model.summary)}</p>` : '<span></span>'}${renderContents(model, t)}</section>` : ''}
    <article class="guide-print-body">${body}</article>
    ${referenceSections}
    <footer class="guide-print-footer"><span><strong>${PRINT_BRAND}</strong> · ${escapeHtml(t('guides.print.footerHint'))}</span><span>${escapeHtml(t('guides.print.preparedAt', { value: model.preparedAt }))}</span></footer>
  </main>
  <script>
    const guidePrintThemeStorageKey='rbf-guide-print-theme'
    function updateGuidePrintThemeButtons(theme){
      document.querySelectorAll('[data-theme-choice]').forEach((button)=>{
        button.setAttribute('aria-pressed',String(button.dataset.themeChoice===theme))
      })
    }
    function setGuidePrintTheme(theme){
      if(theme==='system') document.documentElement.removeAttribute('data-theme')
      else document.documentElement.setAttribute('data-theme',theme)
      updateGuidePrintThemeButtons(theme)
      try{localStorage.setItem(guidePrintThemeStorageKey,theme)}catch{}
    }
    let savedGuidePrintTheme='system'
    try{savedGuidePrintTheme=localStorage.getItem(guidePrintThemeStorageKey)||'system'}catch{}
    if(!['system','light','dark'].includes(savedGuidePrintTheme)) savedGuidePrintTheme='system'
    setGuidePrintTheme(savedGuidePrintTheme)
  </script>
</body>
</html>`
}

function openGuidePrintWindow(guide, options = {}) {
  const popup = window.open('', '_blank')
  if (!popup) throw new Error('Guide print view could not be opened.')
  popup.opener = null
  popup.document.open()
  popup.document.write(createGuidePrintHtml(guide, options))
  popup.document.close()
  popup.focus()
  return popup
}

export {
  createGuidePrintHtml,
  createGuidePrintModel,
  escapeHtml,
  extractGuideHeadings,
  openGuidePrintWindow,
}
