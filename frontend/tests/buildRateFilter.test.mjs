import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const listPage = new URL('../src/modules/builds/composables/useBuildListPage.js', import.meta.url)
const myBuildsPage = new URL('../src/modules/builds/composables/useMyBuildsPage.js', import.meta.url)
const api = new URL('../src/modules/builds/api/builds.js', import.meta.url)

test('build library and personal builds pass the selected ship rate to the API', async () => {
  const [listSource, mineSource, apiSource] = await Promise.all([
    readFile(listPage, 'utf8'),
    readFile(myBuildsPage, 'utf8'),
    readFile(api, 'utf8'),
  ])

  assert.match(listSource, /const shipRate = ref\(''\)/)
  assert.match(listSource, /listBuilds\([^)]*shipRate\.value\)/s)
  assert.match(listSource, /watch\(\[search, buildType, shipRate, classification\]/)
  assert.match(mineSource, /listMyBuilds\([^)]*shipRate\.value\)/s)
  assert.match(apiSource, /ship_rate: shipRate/)
})
