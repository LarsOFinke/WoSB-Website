import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const pages = [
  ['admin/pages/AdminPage.vue', 'useAdminWorkspace'],
  ['admin/pages/MasterDataPage.vue', 'useMasterDataWorkspace'],
  ['builds/pages/BuildCreatePage.vue', 'useBuildDesigner'],
  ['builds/pages/BuildDetailPage.vue', 'useBuildDetailPage'],
  ['accounts/pages/ProfilePage.vue', 'useProfilePage'],
  ['calendar/pages/CalendarPage.vue', 'useCalendarPage'],
  ['fleet/pages/FleetManagePage.vue', 'useFleetManagePage'],
  ['groups/pages/GroupDetailPage.vue', 'useGroupDetailPage'],
  ['onboarding/pages/NewcomerGuidePage.vue', 'useNewcomerGuidePage'],
  ['squads/pages/SquadDetailPage.vue', 'useSquadDetailPage'],
]

test('complex pages delegate state and use-cases to dedicated page models', async () => {
  for (const [relativePath, composable] of pages) {
    const source = await readFile(new URL(`../src/modules/${relativePath}`, import.meta.url), 'utf8')
    const script = source.match(/<script setup>([\s\S]*?)<\/script>/)?.[1] || ''
    assert.match(script, new RegExp(`${composable}\\(`), `${relativePath} should invoke ${composable}`)
    assert.doesNotMatch(script, /\/api\//, `${relativePath} should not call APIs directly`)
    assert.doesNotMatch(script, /async function/, `${relativePath} should not own async use-cases`)
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
