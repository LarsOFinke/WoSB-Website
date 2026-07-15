export function createGroupJoinForm() {
  return { display_name: '', fleet_name: '', ship_id: '', build_id: '', note: '' }
}

export function isGroupShipAllowed(group, rate) {
  if (!group || !rate) return !group?.min_ship_rate && !group?.max_ship_rate
  if (group.min_ship_rate && rate > group.min_ship_rate) return false
  if (group.max_ship_rate && rate < group.max_ship_rate) return false
  return true
}

export function groupRateRequirement(group, t) {
  if (!group) return t('groups.detail.anyRate')
  const minRate = group.min_ship_rate
  const maxRate = group.max_ship_rate
  if (minRate && maxRate) return t('groups.detail.rateRangeRequirement', { max: maxRate, min: minRate })
  if (minRate) return t('groups.detail.minRateRequirement', { rate: minRate })
  if (maxRate) return t('groups.detail.maxRateRequirement', { rate: maxRate })
  return t('groups.detail.anyRate')
}

export function formatGroupDateTime(value, locale) {
  if (!value) return ''
  return new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' })
}

export function groupSchedule(group, t, locale) {
  if (!group?.scheduled_start_at) return t('groups.detail.noSchedule')
  const start = formatGroupDateTime(group.scheduled_start_at, locale)
  const end = group.scheduled_end_at ? formatGroupDateTime(group.scheduled_end_at, locale) : null
  return end ? `${start} – ${end}` : start
}

export function groupMemberShipLabel(member, t) {
  if (member.build) return `${member.build.build_name} · ${member.build.ship.name}`
  if (member.ship) return `${member.ship.name} · ${t('common.rate')} ${member.ship.rate}`
  return member.ship_name || t('groups.detail.noShip')
}

export function groupJoinPayload(form, user, selectedShip) {
  return {
    display_name: form.display_name || user?.display_name || user?.username || '',
    fleet_name: form.fleet_name || null,
    ship_id: form.build_id ? null : (form.ship_id ? Number(form.ship_id) : null),
    build_id: form.build_id ? Number(form.build_id) : null,
    ship_name: selectedShip?.name || null,
    ship_rate: selectedShip?.rate || null,
    note: form.note || null,
  }
}
