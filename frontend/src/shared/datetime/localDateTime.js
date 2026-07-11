function pad2(value) {
  return String(value).padStart(2, '0')
}

export function dateInputValue(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`
}

export function timeInputValue(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return ''
  return `${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}

export function isValidDateInput(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''))
  if (!match) return false
  const [, yearText, monthText, dayText] = match
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const date = new Date(year, month - 1, day)
  return year >= 1000
    && year <= 9999
    && date.getFullYear() === year
    && date.getMonth() === month - 1
    && date.getDate() === day
}

export function isValidTimeInput(value) {
  const match = /^(\d{2}):(\d{2})$/.exec(String(value || ''))
  if (!match) return false
  const hour = Number(match[1])
  const minute = Number(match[2])
  return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59
}

export function localDateFromInputs(dateValue, timeValue = '00:00') {
  if (!isValidDateInput(dateValue) || !isValidTimeInput(timeValue)) return null
  const [year, month, day] = dateValue.split('-').map(Number)
  const [hour, minute] = timeValue.split(':').map(Number)
  return new Date(year, month - 1, day, hour, minute, 0, 0)
}

export function localDateTimeValue(dateValue, timeValue) {
  return localDateFromInputs(dateValue, timeValue) ? `${dateValue}T${timeValue}` : ''
}

export function splitLocalDateTime(value) {
  const match = /^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})/.exec(String(value || ''))
  if (match && isValidDateInput(match[1]) && isValidTimeInput(match[2])) {
    return { date: match[1], time: match[2] }
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return { date: '', time: '' }
  return { date: dateInputValue(parsed), time: timeInputValue(parsed) }
}
