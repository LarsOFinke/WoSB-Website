import assert from 'node:assert/strict'
import test from 'node:test'

import {
  extractGuideHeadings,
  formatGuideDate,
  guideHeadingNavigation,
  stripInlineMarkdown,
} from '../src/modules/guides/domain/guidePresentation.js'

test('guide presentation strips inline markdown without losing labels', () => {
  assert.equal(
    stripInlineMarkdown('**Fleet** [signals](https://example.test) `quickly`'),
    'Fleet signals quickly',
  )
})

test('guide headings receive stable navigation metadata', () => {
  const source = [
    '# **Preparation**',
    'Body copy',
    '## [Execution](https://example.test)',
    '#### Ignored depth',
  ].join('\n')

  assert.deepEqual(extractGuideHeadings(source), [
    { level: 1, label: 'Preparation', number: '01' },
    { level: 2, label: 'Execution', number: '02' },
  ])
  assert.deepEqual(guideHeadingNavigation(source, 'section'), [
    { level: 1, label: 'Preparation', number: '01', id: 'section-1' },
    { level: 2, label: 'Execution', number: '02', id: 'section-2' },
  ])
})

test('guide dates provide a readable fallback and deterministic locale output', () => {
  assert.equal(formatGuideDate(''), '—')
  assert.equal(formatGuideDate('not-a-date'), '—')
  assert.equal(formatGuideDate('2026-07-26T10:00:00Z', 'de-DE'), '26.07.2026')
})
