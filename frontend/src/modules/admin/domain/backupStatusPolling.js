export const BACKUP_STATUS_POLL_INTERVAL_MS = 2500
export const BACKUP_SNAPSHOT_POLL_INTERVAL_MS = 7500
export const BACKUP_STATUS_MAX_BACKOFF_MS = 30000

export function backupStatusPollDelay({ message = '', failures = 0 } = {}) {
  const boundedFailures = Math.max(0, Math.min(Number(failures) || 0, 8))
  if (boundedFailures > 0) {
    return Math.min(
      BACKUP_STATUS_POLL_INTERVAL_MS * (2 ** boundedFailures),
      BACKUP_STATUS_MAX_BACKOFF_MS,
    )
  }

  const normalizedMessage = String(message).toLowerCase()
  if (normalizedMessage.includes('preparing') || normalizedMessage.includes('coordinated')) {
    return BACKUP_SNAPSHOT_POLL_INTERVAL_MS
  }
  return BACKUP_STATUS_POLL_INTERVAL_MS
}
