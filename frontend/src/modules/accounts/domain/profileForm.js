export const PROFILE_FOCUS_OPTIONS = [
  'pve_farming',
  'pve_imp_hunting',
  'pve_general',
  'pvp_open_world',
  'pvp_arena',
  'pvp_general',
  'trading',
  'other',
]

export function createProfileForm() {
  return {
    username: '',
    display_name: '',
    fleet_name: '',
    fleet_id: null,
    fleet_membership_id: null,
    fleet_membership_status: '',
    fleet_membership_role: '',
    preferred_focus: '',
    availability: '',
    timezone: '',
    discord_handle: '',
    preferred_ship_ids: [],
    preferred_role_ids: [],
    note: '',
    role: 'user',
  }
}

export function createPasswordForm() {
  return { current_password: '', new_password: '', repeat_password: '' }
}

export function hydrateProfileForm(form, user) {
  Object.assign(form, {
    username: user.username || '',
    display_name: user.display_name || '',
    fleet_name: user.fleet_name || '',
    fleet_id: user.fleet_id || null,
    fleet_membership_id: user.fleet_membership_id || null,
    fleet_membership_status: user.fleet_membership_status || '',
    fleet_membership_role: user.fleet_membership_role || '',
    preferred_focus: user.preferred_focus || '',
    availability: user.availability || '',
    timezone: user.timezone || '',
    discord_handle: user.discord_handle || '',
    preferred_ship_ids: [...(user.preferred_ship_ids || [])],
    preferred_role_ids: [...(user.preferred_role_ids || [])],
    note: user.note || '',
    role: user.role || 'user',
  })
}

export function profileInitials(form) {
  const parts = (form.display_name || form.username || 'RBF').trim().split(/\s+/).filter(Boolean)
  return parts.slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'RBF'
}

export function profileCompletion(form, hasOfficialFleetLink) {
  const checks = [
    Boolean(form.display_name.trim()),
    Boolean(form.preferred_focus),
    Boolean(form.note.trim()),
    Boolean(form.timezone.trim() || form.availability.trim()),
    Boolean(form.preferred_ship_ids.length || form.preferred_role_ids.length),
    hasOfficialFleetLink || Boolean(form.fleet_name.trim()),
  ]
  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
}

export function profileUpdatePayload(form, hasOfficialFleetLink) {
  return {
    display_name: form.display_name,
    fleet_name: hasOfficialFleetLink ? null : form.fleet_name || null,
    preferred_focus: form.preferred_focus || null,
    availability: form.availability || null,
    timezone: form.timezone || null,
    discord_handle: form.discord_handle || null,
    preferred_ship_ids: form.preferred_ship_ids,
    preferred_role_ids: form.preferred_role_ids,
    note: form.note || null,
  }
}
