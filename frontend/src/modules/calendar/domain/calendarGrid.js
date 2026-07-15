export function monthGridRange(activeMonth) {
  const year = activeMonth.getFullYear()
  const month = activeMonth.getMonth()
  const firstOfMonth = new Date(year, month, 1)
  const lastOfMonth = new Date(year, month + 1, 0)
  const gridStart = new Date(firstOfMonth)
  gridStart.setDate(firstOfMonth.getDate() - ((firstOfMonth.getDay() + 6) % 7))
  const gridEnd = new Date(lastOfMonth)
  gridEnd.setDate(lastOfMonth.getDate() + (6 - ((lastOfMonth.getDay() + 6) % 7)))
  gridEnd.setHours(23, 59, 59, 999)
  return { gridStart, gridEnd }
}

export function daysInRange({ gridStart, gridEnd }) {
  const days = []
  const cursor = new Date(gridStart)
  while (cursor <= gridEnd) {
    days.push(new Date(cursor))
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}

export function dateKey(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-')
}

export function isSameDay(left, right) {
  return dateKey(left) === dateKey(right)
}

export function eventsOnDate(events, date) {
  const key = dateKey(date)
  return events.filter((event) => {
    const start = new Date(event.start_at)
    const end = new Date(new Date(event.end_at).getTime() - 1)
    const cursor = new Date(start)
    cursor.setHours(0, 0, 0, 0)
    const endDay = new Date(end)
    endDay.setHours(0, 0, 0, 0)

    while (cursor <= endDay) {
      if (dateKey(cursor) === key) return true
      cursor.setDate(cursor.getDate() + 1)
    }
    return false
  })
}

export function calendarDayClasses({ date, activeMonth, today, selectedDate, events }) {
  return {
    'is-outside-month': date.getMonth() !== activeMonth.getMonth(),
    'is-today': isSameDay(date, today),
    'is-selected': isSameDay(date, selectedDate),
    'has-events': eventsOnDate(events, date).length > 0,
  }
}

export function filtersForScope(scope) {
  if (scope === 'fleet') return { fleetOnly: true, squadId: '' }
  if (scope.startsWith('squad:')) return { fleetOnly: false, squadId: scope.split(':')[1] }
  return { fleetOnly: false, squadId: '' }
}

export function newEventTargetForScope(scope) {
  if (scope.startsWith('squad:')) {
    return { path: '/calendar/new', query: { squad: scope.split(':')[1] } }
  }
  return '/calendar/new'
}
