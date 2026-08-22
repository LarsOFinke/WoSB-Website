import assert from 'node:assert/strict'
import test from 'node:test'

import {
  BACKUP_STATUS_MAX_BACKOFF_MS,
  backupStatusPollDelay,
} from '../src/modules/admin/domain/backupStatusPolling.js'

test('backup polling slows down during the consistency snapshot', () => {
  assert.equal(backupStatusPollDelay({ message: 'Preparing the coordinated backup set.' }), 7500)
  assert.equal(backupStatusPollDelay({ message: 'Transferring verified artifacts.' }), 2500)
})

test('backup polling applies bounded exponential backoff after temporary API outages', () => {
  assert.equal(backupStatusPollDelay({ failures: 1 }), 5000)
  assert.equal(backupStatusPollDelay({ failures: 2 }), 10000)
  assert.equal(backupStatusPollDelay({ failures: 8 }), BACKUP_STATUS_MAX_BACKOFF_MS)
})
