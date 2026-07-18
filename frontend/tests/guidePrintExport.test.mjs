import assert from 'node:assert/strict'
import test from 'node:test'

import {
  createGuidePrintHtml,
  createGuidePrintModel,
  extractGuideHeadings,
} from '../src/modules/guides/guidePrintExport.js'

const messages = {
  'guides.categories.combat': 'Combat',
  'guides.print.attachmentFallback': 'Attachment',
  'guides.print.attachmentsTitle': 'Attachments and references',
  'guides.print.author': 'Author',
  'guides.print.brandMotto': 'Discipline · Honour · Victory',
  'guides.print.contentsTitle': 'Contents',
  'guides.print.fallbackTitle': 'Guide',
  'guides.print.footerHint': 'Prepared for offline fleet use.',
  'guides.print.linkedBuildEyebrow': 'Linked build',
  'guides.print.linkedBuildsTitle': 'Linked builds',
  'guides.print.preparedAt': 'Prepared {value}',
  'guides.print.printAction': 'Print or save as PDF',
  'guides.print.source': 'Source',
  'guides.print.themeDark': 'Dark',
  'guides.print.themeLabel': 'Appearance',
  'guides.print.themeLight': 'Light',
  'guides.print.themeSystem': 'System',
  'guides.print.unknownAuthor': 'Unknown author',
  'guides.print.updated': 'Updated',
  'builds.list.crew': 'Crew {current}/{max}',
  'builds.list.upgradeSummary': '{used}/{max} upgrades',
  'builds.print.fallbackTitle': 'Build sheet',
  'builds.types.balanced': 'Balanced',
  'buildEmbeds.inlineMissing': 'Build #{id} is not linked.',
  'common.rate': 'Rate',
  'files.inlineMissing': 'File #{id} is not attached.',
  'files.kind.image': 'Image',
  'files.kind.pdf': 'PDF',
}

function t(key, values = {}) {
  return String(messages[key] || key).replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? '')
}

const guide = {
  id: 42,
  title: 'Port Battle Preparation',
  category: 'combat',
  summary: 'Prepare the fleet, crew and signals before entering the port.',
  body: '# Preparation\n\n- Scout the entrance\n- Confirm signals\n\n[[file:10|large]]\n\n## Execution\n\n1. Take the entrance\n2. Hold formation\n\n[[build:5|card]]',
  owner: { display_name: 'Fleet Combat Office' },
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-12T12:30:00Z',
  attachments: [
    { id: 10, original_name: 'port-map.png', mime_type: 'image/png', size_bytes: 2048, public_url: '/uploads/port-map.png' },
    { id: 11, original_name: 'signals.pdf', mime_type: 'application/pdf', size_bytes: 4096, public_url: '/uploads/signals.pdf' },
  ],
  builds: [
    {
      id: 5,
      build_name: 'Harbour Breaker',
      build_type: 'balanced',
      ship: { name: 'Leopard', rate: 3, crew_capacity: 130 },
      ship_stats: { crew_total: 120, crew_capacity: 144, upgrade_slots_used: 3, upgrade_slots_available: 4 },
    },
    {
      id: 6,
      build_name: 'Screening Frigate',
      build_type: 'balanced',
      ship: { name: 'Surprise', rate: 5, crew_capacity: 80 },
      ship_stats: { crew_total: 72, crew_capacity: 80, upgrade_slots_used: 2, upgrade_slots_available: 4 },
    },
  ],
}

const helpers = {
  t,
  formatDate: (value) => new Date(value).toISOString().slice(0, 10),
  locationObject: { origin: 'https://fleet.example' },
  renderMarkdown: (source) => `<p>${source}</p>`,
}

test('guide print model preserves reading order and separates unused references', () => {
  const model = createGuidePrintModel(guide, helpers)

  assert.equal(model.title, 'Port Battle Preparation')
  assert.deepEqual(model.tableOfContents.map((heading) => heading.label), ['Preparation', 'Execution'])
  assert.deepEqual(model.parts.map((part) => part.type), ['text', 'file', 'text', 'build'])
  assert.deepEqual(model.attachments.map((file) => file.name), ['signals.pdf'])
  assert.deepEqual(model.builds.map((build) => build.name), ['Screening Frigate'])
  assert.equal(model.sourceUrl, 'https://fleet.example/guides/42')
})

test('guide print HTML is A4-ready and keeps rich references readable offline', () => {
  const html = createGuidePrintHtml(guide, helpers)

  assert.match(html, /@page\{size:A4 portrait/)
  assert.match(html, /Port Battle Preparation/)
  assert.match(html, /https:\/\/fleet\.example\/uploads\/port-map\.png/)
  assert.match(html, /Harbour Breaker/)
  assert.match(html, /Screening Frigate/)
  assert.match(html, /signals\.pdf/)
  assert.match(html, /break-inside:avoid-page/)
  assert.match(html, /Print or save as PDF/)
  assert.match(html, /prefers-color-scheme:dark/)
  assert.match(html, /data-theme-choice="system"/)
  assert.match(html, /data-theme-choice="light"/)
  assert.match(html, /data-theme-choice="dark"/)
  assert.match(html, /aria-pressed="true"/)
  assert.match(html, /rbf-guide-print-theme/)
})

test('guide print metadata is escaped before entering the standalone document', () => {
  const html = createGuidePrintHtml({ ...guide, title: '<script>alert(1)</script>' }, helpers)

  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/)
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/)
})

test('guide heading extraction ignores prose and strips inline markdown', () => {
  assert.deepEqual(
    extractGuideHeadings('Intro\n\n# **First** section\nText\n### [Reference](https://example.test)'),
    [
      { level: 1, label: 'First section', number: '01' },
      { level: 3, label: 'Reference', number: '02' },
    ],
  )
})
