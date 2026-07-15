export function createSquadEditForm() {
  return { name: '', description: '', focus: '', maxMembers: '' }
}

export function createSquadMemberForm() {
  return { fleetMembershipId: '', role: 'member', note: '' }
}

export function availableSquadRoster(roster, members = []) {
  const currentIds = new Set(members.map((member) => member.fleet_membership_id))
  return roster.filter((member) => !currentIds.has(member.fleet_membership_id))
}

export function syncSquadForms(squad, editForm, memberDrafts) {
  if (!squad) return
  Object.assign(editForm, {
    name: squad.name || '',
    description: squad.description || '',
    focus: squad.focus || '',
    maxMembers: squad.max_members || '',
  })

  for (const key of Object.keys(memberDrafts)) delete memberDrafts[key]
  for (const member of squad.members || []) {
    memberDrafts[member.id] = { role: member.squad_role, note: member.note || '' }
  }
}

export function squadUpdatePayload(form) {
  return {
    name: form.name,
    description: form.description || null,
    focus: form.focus || null,
    max_members: form.maxMembers ? Number(form.maxMembers) : null,
  }
}

export function squadMemberCreatePayload(form) {
  return {
    fleet_membership_id: Number(form.fleetMembershipId),
    role: form.role,
    note: form.note || null,
  }
}

export function squadMemberUpdatePayload(draft) {
  return { role: draft.role, note: draft.note || null }
}

export function canRemoveSquadMember(squad, member) {
  if (!squad?.can_manage || member.squad_role === 'leader') return false
  return squad.can_administer || member.squad_role === 'member'
}
