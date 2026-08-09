import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { globalStyleFiles, readGlobalStyles } from './helpers/readGlobalStyles.mjs'
import test from 'node:test'
import { readCssBundle } from './helpers/readCssBundle.mjs'

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
  assert.equal(files[0], '00-tokens.css')
  assert.ok(files.length >= 50)
  assert.equal(new Set(files).size, files.length)
  assert.match(source, /^:root\s*\{/)
  assert.equal((source.match(/^:root\s*\{/gm) || []).length, 1)
  assert.doesNotMatch(source, /@import/)
  assert.match(source, /\.build-editor-delete-action\s*\{/)
})

test('large integration workspaces keep their styles with the owning feature', async () => {
  const [buildStyles, discoveryStyles] = await Promise.all([
    readFile(new URL('../src/modules/builds/styles/buildWorkspace.css', import.meta.url), 'utf8'),
    readFile(new URL('../src/shared/styles/discovery.css', import.meta.url), 'utf8'),
  ])
  const adminStyles = readCssBundle([
    '../src/modules/admin/styles/adminWebhookEditorDrawer.css',
    '../src/modules/admin/styles/adminDatabaseBackups.css',
    '../src/modules/admin/styles/adminRaidHelper.css',
  ], import.meta.url)
  assert.match(adminStyles, /\.webhook-editor-layer\s*\{/)
  assert.match(adminStyles, /\.backup-workspace\s*\{/)
  assert.match(buildStyles, /\.build-detail-command-frame\s*\{/)
  assert.match(discoveryStyles, /\.discovery-tile-grid\s*\{/)
})
