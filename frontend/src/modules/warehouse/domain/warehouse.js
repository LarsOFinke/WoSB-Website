export function createWarehouseDraft(fleetId = '') {
  return {
    fleet_id: fleetId,
    holder_mode: 'member',
    member_user_id: '',
    custom_holder_name: '',
    port: '',
    resource: '',
    amount: 0,
    reserved: false,
    collection_status: 'up_for_collection',
    version: null,
  }
}

export function warehouseDraftFromEntry(entry) {
  return {
    fleet_id: entry.fleet_id,
    holder_mode: entry.member_user_id ? 'member' : 'custom',
    member_user_id: entry.member_user_id || '',
    custom_holder_name: entry.custom_holder_name || '',
    port: entry.port,
    resource: entry.resource,
    amount: entry.amount,
    reserved: Boolean(entry.reserved),
    collection_status: entry.collection_status || 'in_warehouse',
    version: entry.version,
  }
}

export function warehouseDraftIssue(draft) {
  if (!Number.isInteger(Number(draft.fleet_id)) || Number(draft.fleet_id) < 1) return 'fleet'
  if (draft.holder_mode === 'member' && (!Number.isInteger(Number(draft.member_user_id)) || Number(draft.member_user_id) < 1)) return 'member'
  if (draft.holder_mode === 'custom' && !String(draft.custom_holder_name || '').trim()) return 'customHolder'
  if (!String(draft.port || '').trim()) return 'port'
  if (!String(draft.resource || '').trim()) return 'resource'
  if (!['up_for_collection', 'in_warehouse'].includes(draft.collection_status)) return 'collectionStatus'
  const amount = Number(draft.amount)
  if (!Number.isInteger(amount) || amount < 0 || amount > 999999999) return 'amount'
  return ''
}

export function warehousePayload(draft, { updating = false } = {}) {
  const payload = {
    fleet_id: Number(draft.fleet_id),
    member_user_id: draft.holder_mode === 'member' ? Number(draft.member_user_id) : null,
    custom_holder_name: draft.holder_mode === 'custom'
      ? String(draft.custom_holder_name).trim()
      : null,
    port: String(draft.port).trim(),
    resource: String(draft.resource).trim(),
    amount: Number(draft.amount),
    reserved: Boolean(draft.reserved),
    collection_status: draft.collection_status,
  }
  if (updating) payload.version = Number(draft.version)
  return payload
}

export function formatWarehouseAmount(value, locale = 'en') {
  return new Intl.NumberFormat(locale).format(Number(value) || 0)
}
