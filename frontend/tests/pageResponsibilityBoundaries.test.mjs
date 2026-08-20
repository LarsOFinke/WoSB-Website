import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const modulesRoot = fileURLToPath(new URL('../src/modules', import.meta.url))

async function collectRoutePages(directory = modulesRoot) {
  const pages = []
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      pages.push(...await collectRoutePages(target))
    } else if (entry.name.endsWith('Page.vue') && target.includes(`${path.sep}pages${path.sep}`)) {
      pages.push(target)
    }
  }
  return pages.sort()
}

function scriptSetup(source) {
  return source.match(/<script setup>([\s\S]*?)<\/script>/)?.[1] || ''
}

test('every route page delegates stateful work to a page model', async () => {
  const pages = await collectRoutePages()
  assert.equal(pages.length, 42, 'update the architecture expectation when route pages are added or removed')

  for (const page of pages) {
    const relativePath = path.relative(modulesRoot, page)
    const script = scriptSetup(await readFile(page, 'utf8'))
    assert.match(
      script,
      /\buse(?:[A-Z][A-Za-z0-9]+Page|AdminWorkspace|MasterDataWorkspace|BuildDesigner|FleetManagePage|NewcomerGuidePage)\s*\(/,
      `${relativePath} should invoke a dedicated page model`,
    )
    assert.doesNotMatch(script, /\/api\//, `${relativePath} should not import API transport modules`)
    assert.doesNotMatch(script, /\basync\s+(?:function|\()/, `${relativePath} should not own async use-cases`)
    assert.doesNotMatch(script, /\bonMounted\s*\(/, `${relativePath} should not own lifecycle-driven loading`)
  }
})

test('build details show upgrade effects once in the live calculation', async () => {
  const source = await readFile(
    new URL('../src/modules/builds/pages/BuildDetailPage.vue', import.meta.url),
    'utf8',
  )

  assert.match(source, /:effect-rows="activeEffectRows"/)
  assert.doesNotMatch(source, /build-detail-effect-row/)
  assert.doesNotMatch(source, /v-for="effect in activeEffectRows"/)
})

test('build creation guards mortar data while the selected ship is still loading', async () => {
  const source = await readFile(
    new URL('../src/modules/builds/pages/BuildCreatePage.vue', import.meta.url),
    'utf8',
  )

  assert.match(
    source,
    /computed\(\(\) => selectedShip\.value\?\.mortar_modification \?\? null\)/,
  )
  assert.match(source, /v-if="mortarModification"/)
  assert.doesNotMatch(source, /selectedShip\.mortar_modification/)
})
