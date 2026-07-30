import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const panelPath = new URL('../src/modules/admin/components/SystemOperationsPanel.vue', import.meta.url)

test('system update panel exposes only privacy-minimal status fields', async () => {
  const panel = await readFile(panelPath, 'utf8')
  for (const forbidden of ['requested_by', 'commit_before', 'commit_after', 'current_commit', 'available_commit', 'log_tail']) {
    assert.equal(panel.includes(forbidden), false, `update panel must not render ${forbidden}`)
  }
  assert.match(panel, /update\.value\.state/)
  assert.match(panel, /update\.started_at/)
  assert.match(panel, /update\.finished_at/)
})


test('system operations expose a confirmed application-only restart', async () => {
  const panel = await readFile(panelPath, 'utf8')
  assert.match(panel, /trigger\('restart'\)/)
  assert.match(panel, /admin\.system\.restartConfirm/)
  assert.match(panel, /admin\.system\.restartRequestAccepted/)
  assert.match(panel, /system-restart-action/)
  assert.match(panel, /danger-action/)
})
