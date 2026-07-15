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
