import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { globalStyleFiles, readGlobalStyles } from './helpers/readGlobalStyles.mjs'
import test from 'node:test'

const buildModelUrl = new URL('../src/modules/builds/composables/useBuildListPage.js', import.meta.url)
const guideModelUrl = new URL('../src/modules/guides/composables/useGuideListPage.js', import.meta.url)

for (const [label, sourceUrl, loader] of [
  ['builds', buildModelUrl, 'loadBuilds'],
  ['guides', guideModelUrl, 'loadGuides'],
]) {
  test(`${label} are loaded and visible by default`, async () => {
    const source = await readFile(sourceUrl, 'utf8')
    assert.match(source, /const showAll = ref\(true\)/)
    assert.ok(source.includes(`onMounted(${loader})`))
    assert.match(source, /showAll\.value = !hasFilters\.value/)
    assert.match(source, /function resetDiscovery\(\)[\s\S]*showAll\.value = true/)
  })
}

test('the global stylesheet is delivered through one deterministic JavaScript cascade manifest', () => {
  const files = globalStyleFiles()
  const source = readGlobalStyles()
  assert.deepEqual(files, [
    '00-tokens.css',
    '10-foundation.css',
    '20-layout.css',
    '30-shell.css',
    '40-navigation-and-portal.css',
    '50-domain-workspaces.css',
    '60-operations.css',
    '70-integrations.css',
  ])
  assert.match(source, /^:root\s*\{/)
  assert.equal((source.match(/^:root\s*\{/gm) || []).length, 1)
  assert.doesNotMatch(source, /@import/)
  assert.match(source, /\.webhook-editor-layer\s*\{/)
  assert.match(source, /\.build-editor-delete-action\s*\{/)
})
