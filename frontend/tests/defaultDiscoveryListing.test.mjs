import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
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

test('the global stylesheet is delivered as one ordered cascade', async () => {
  const source = await readFile(new URL('../src/styles/main.css', import.meta.url), 'utf8')
  assert.match(source, /^:root\s*\{/)
  assert.doesNotMatch(source, /@import/)
  assert.match(source, /\.webhook-editor-layer\s*\{/)
  assert.match(source, /\.build-editor-delete-action\s*\{/)
})
