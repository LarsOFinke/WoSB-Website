function positiveInteger(value) {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

export function upcomingEventsForSquads(events, squads, now = new Date()) {
  const squadIds = new Set((squads || []).map((squad) => positiveInteger(squad?.id)).filter(Boolean))
  const threshold = now instanceof Date && !Number.isNaN(now.getTime()) ? now.getTime() : Date.now()

  return (events || [])
    .filter((event) => {
      const squadId = positiveInteger(event?.squad_id)
      if (!squadId || !squadIds.has(squadId) || event?.is_cancelled) return false
      const end = new Date(event.end_at || event.start_at)
      return !Number.isNaN(end.getTime()) && end.getTime() >= threshold
    })
    .sort((left, right) => new Date(left.start_at) - new Date(right.start_at))
}
