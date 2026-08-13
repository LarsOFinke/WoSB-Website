import assert from 'node:assert/strict'
import test from 'node:test'

import { dateFromRouteQuery, dateKey, daysInRange, eventsOnDate, filtersForScope, monthGridRange } from '../src/modules/calendar/domain/calendarGrid.js'
import { profileCompletion, profileInitials, profileUpdatePayload } from '../src/modules/accounts/domain/profileForm.js'
import { filterFleetMemberships, hasFleetMemberPermission, membershipFieldPayload } from '../src/modules/fleet/domain/fleetMemberships.js'
import { createGuideDraft, guidePayload, moveArrayItem, moveSelectedItem } from '../src/modules/onboarding/domain/newcomerGuideDraft.js'
import { resourceIcon, topicKind, topicResourceCount, topicSummary } from '../src/modules/onboarding/domain/newcomerGuidePresentation.js'
import { canRemoveSquadMember, squadUpdatePayload } from '../src/modules/squads/domain/squadManagement.js'
import { groupJoinPayload, isGroupShipAllowed } from '../src/modules/groups/domain/groupDetail.js'
import { formatBuildModifier, inventoryCategory, slotQuantity } from '../src/modules/builds/domain/buildDetailPresentation.js'

test('calendar grid covers complete Monday-to-Sunday weeks', () => {
  const range = monthGridRange(new Date(2026, 6, 1))
  const days = daysInRange(range)
  assert.equal(range.gridStart.getDay(), 1)
  assert.equal(range.gridEnd.getDay(), 0)
  assert.equal(days.length % 7, 0)
  assert.equal(dateKey(days[0]), '2026-06-29')
})

test('calendar events are included on every covered day and scope filters stay explicit', () => {
  const events = [{ start_at: '2026-07-15T22:00:00.000Z', end_at: '2026-07-17T01:00:00.000Z' }]
  assert.equal(eventsOnDate(events, new Date('2026-07-16T12:00:00.000Z')).length, 1)
  assert.deepEqual(filtersForScope('fleet'), { fleetOnly: true, squadId: '' })
  assert.deepEqual(filtersForScope('squad:42'), { fleetOnly: false, squadId: '42' })
})

test('calendar deep links select a valid event date and reject invalid dates', () => {
  const fallback = new Date(2026, 0, 5)
  assert.equal(dateKey(dateFromRouteQuery('2026-07-15', fallback)), '2026-07-15')
  assert.equal(dateKey(dateFromRouteQuery('2026-02-31', fallback)), '2026-01-05')
  assert.equal(dateKey(dateFromRouteQuery(undefined, fallback)), '2026-01-05')
})

test('profile presentation and payload mapping are pure', () => {
  const form = {
    username: 'captain', display_name: 'Anne Bonny', fleet_name: 'RBF', fleet_id: 1,
    fleet_membership_status: 'active', preferred_focus: 'pvp_general', note: 'Ready',
    timezone: 'Europe/Berlin', availability: '', preferred_ship_ids: [3],
    preferred_role_ids: [], discord_handle: '',
  }
  assert.equal(profileInitials(form), 'AB')
  assert.equal(profileCompletion(form, true), 100)
  assert.equal(profileUpdatePayload(form, true).fleet_name, null)
})

test('fleet membership filtering and permissions use backend management metadata', () => {
  const memberships = [{
    status: 'active', role: 'member', assignment: 'Scout', user: { display_name: 'Grace', username: 'grace' },
    management: { can_edit_directory: true, can_change_role: false, can_change_status: false },
  }]
  assert.equal(filterFleetMemberships(memberships, { search: 'scout', status: 'active' }).length, 1)
  assert.equal(hasFleetMemberPermission(memberships[0]), true)
  assert.deepEqual(membershipFieldPayload('assignment', ''), { assignment: null })
})

test('newcomer guide drafts normalize linked and external resources', () => {
  const source = {
    title: 'Start', intro: 'Welcome', blocks: [{
      block_type: 'resources', title: 'Links', body: '', resources: [
        { resource_type: 'external', href: 'https://example.test', label: 'Docs' },
      ],
    }],
  }
  const draft = createGuideDraft(source)
  assert.equal(draft.blocks[0].resources[0].url, 'https://example.test')
  assert.equal(guidePayload(draft).blocks[0].resources[0].url, 'https://example.test')
  assert.equal(moveArrayItem([1, 2, 3], 0, 1), true)
  const folders = ['briefing', 'builds', 'operations']
  assert.equal(moveSelectedItem(folders, 1, 1, -1), 0)
  assert.deepEqual(folders, ['builds', 'briefing', 'operations'])
})

test('newcomer topics expose concise explorer metadata', () => {
  const topic = { block_type: 'resources', body: '## Prepare\nRead the **fleet orders** before sailing.', resources: [{ resource_type: 'build' }] }
  assert.equal(topicSummary(topic, 'Fallback'), 'Prepare Read the fleet orders before sailing.')
  assert.equal(topicResourceCount(topic), 1)
  assert.equal(topicKind(topic), 'resources')
  assert.equal(resourceIcon(topic.resources[0]), 'builds')
})

test('squad and group rules stay outside view components', () => {
  assert.equal(canRemoveSquadMember({ can_manage: true, can_administer: false }, { squad_role: 'member' }), true)
  assert.equal(canRemoveSquadMember({ can_manage: true, can_administer: true }, { squad_role: 'leader' }), false)
  assert.equal(squadUpdatePayload({ name: 'A', description: '', focus: '', maxMembers: '12' }).max_members, 12)
  assert.equal(isGroupShipAllowed({ min_ship_rate: 5, max_ship_rate: 2 }, 3), true)
  assert.equal(isGroupShipAllowed({ min_ship_rate: 5, max_ship_rate: 2 }, 1), false)
  assert.equal(groupJoinPayload({ display_name: '', fleet_name: '', ship_id: '4', build_id: '', note: '' }, { display_name: 'Anne' }, { name: 'Leopard', rate: 4 }).ship_id, 4)
})

test('build detail formatting is separated from page orchestration', () => {
  assert.equal(inventoryCategory('front_weapon_slots'), 'weapon')
  assert.equal(slotQuantity({ item: 'Rum', quantity: 3 }), 3)
  assert.equal(formatBuildModifier({ modifier: 12.5, modifier_kind: 'percent', precision: 1 }), '+12.5%')
})
