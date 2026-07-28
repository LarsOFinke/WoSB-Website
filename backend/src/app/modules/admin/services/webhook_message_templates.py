from __future__ import annotations

def _message(value: str) -> str:
    return value.strip()


DEFAULT_MESSAGES = {
    'build.created': _message(
        """
⚓ **New Build Created**
Build: **{data.build_name}**
Ship: **{data.ship.name}** (Rate `{data.ship.rate}`)
Build type: `{data.build_type}`
Official template: `{data.is_official_template}`
Crew: `{data.sailors}` sailors · `{data.soldiers}` soldiers · `{data.musketeers}` musketeers · `{data.mercenaries}` mercenaries
Owner ID: `{data.owner_id}`
Created by: **{actor.display_name}**
Created at: `{data.created_at}`
🔗 [Open build]({resource.url})
        """
    ),
    'build.removed': _message(
        """
🗑️ **Build Removed**
Build: **{data.build_name}**
Build ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse remaining builds]({resource.url})
        """
    ),
    'build.updated': _message(
        """
🔧 **Build Updated**
Build: **{data.build_name}**
Ship: **{data.ship.name}** (Rate `{data.ship.rate}`)
Build type: `{data.build_type}`
Official template: `{data.is_official_template}`
Crew: `{data.sailors}` sailors · `{data.soldiers}` soldiers · `{data.musketeers}` musketeers · `{data.mercenaries}` mercenaries
Owner ID: `{data.owner_id}`
Updated by: **{actor.display_name}**
Updated at: `{data.updated_at}`
🔗 [Open build]({resource.url})
        """
    ),
    'calendar.event.cancelled': _message(
        """
❌ **Event Cancelled**
Title: **{data.title}**
Category: `{data.category}`
Starts: `{data.start_at}`
Ends: `{data.end_at}`
Location: {data.location}
Squad: **{data.squad.name}** (`{data.squad_id}`)
Cancelled by: **{actor.display_name}**
Cancelled at: `{occurred_at}`
🔗 [Open calendar]({resource.url})
        """
    ),
    'calendar.event.created': _message(
        """
📅 **New Event Created**
Title: **{data.title}**
Category: `{data.category}`
Starts: `{data.start_at}`
Ends: `{data.end_at}`
All day: `{data.all_day}`
Location: {data.location}
Squad: **{data.squad.name}** (`{data.squad_id}`)
Organizer: **{data.owner.display_name}**
Description: {data.description}
Created by: **{actor.display_name}**
🔗 [Open calendar]({resource.url})
        """
    ),
    'calendar.event.updated': _message(
        """
🗓️ **Event Updated**
Title: **{data.title}**
Category: `{data.category}`
Starts: `{data.start_at}`
Ends: `{data.end_at}`
All day: `{data.all_day}`
Location: {data.location}
Squad: **{data.squad.name}** (`{data.squad_id}`)
Organizer: **{data.owner.display_name}**
Description: {data.description}
Updated by: **{actor.display_name}**
🔗 [Open calendar]({resource.url})
        """
    ),
    'forum.thread.created': _message(
        """
💬 **New Forum Thread**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Replies: `{data.reply_count}`
Created at: `{data.created_at}`
Last activity: `{data.last_activity_at}`
Created by: **{actor.display_name}**
🔗 [Open thread]({resource.url})
        """
    ),
    'forum.thread.updated': _message(
        """
✏️ **Forum Thread Updated**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Replies: `{data.reply_count}`
Last activity: `{data.last_activity_at}`
Updated by: **{actor.display_name}**
Updated at: `{data.updated_at}`
🔗 [Open thread]({resource.url})
        """
    ),
    'group.closed': _message(
        """
🔒 **Group Search Closed**
Group: **{data.title}**
Focus: `{data.focus}`
Members: `{data.active_members_count}` / `{data.max_members}`
Closed by: **{actor.display_name}**
Closed at: `{occurred_at}`
🔗 [Open group record]({resource.url})
        """
    ),
    'group.created': _message(
        """
🔎 **New Group Search**
Group: **{data.title}**
Focus: `{data.focus}`
Owner: **{data.owner.display_name}**
Slots: `{data.spots_left}` / `{data.max_members}` available
Allowed ship rates: `{data.max_ship_rate}` to `{data.min_ship_rate}`
Starts: `{data.scheduled_start_at}`
Ends: `{data.scheduled_end_at}`
Expires: `{data.expires_at}`
Created by: **{actor.display_name}**
🔗 [Open group search]({resource.url})
        """
    ),
    'group.member.joined': _message(
        """
🙋 **Member Joined Group Search**
Group: **{data.title}**
Member: **{data.member.display_name}**
Fleet: {data.member.fleet_name}
Ship: **{data.member.ship_name}** (Rate `{data.member.ship_rate}`)
Members: `{data.active_members_count}` / `{data.max_members}`
Remaining slots: `{data.spots_left}`
Joined at: `{occurred_at}`
🔗 [Open group search]({resource.url})
        """
    ),
    'guide.created': _message(
        """
📘 **New Guide Published**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Summary: {data.summary}
Attachments: `{data.attachment_count}`
Linked builds: `{data.build_reference_count}`
Published at: `{data.created_at}`
Created by: **{actor.display_name}**
🔗 [Open guide]({resource.url})
        """
    ),
    'guide.removed': _message(
        """
🗑️ **Guide Removed**
Title: **{data.title}**
Guide ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse remaining guides]({resource.url})
        """
    ),
    'guide.updated': _message(
        """
📝 **Guide Updated**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Summary: {data.summary}
Attachments: `{data.attachment_count}`
Linked builds: `{data.build_reference_count}`
Updated at: `{data.updated_at}`
Updated by: **{actor.display_name}**
🔗 [Open guide]({resource.url})
        """
    ),
    'integration.test': _message(
        """
🧪 **RBF Webhook Test**
Destination: **{destination.name}**
Event: `{event}`
Delivery ID: `{id}`
Occurred at: `{occurred_at}`
Message: {data.message}
        """
    ),
    'newcomer_guide.updated': _message(
        """
🧭 **Newcomer Guide Updated**
Title: **{data.title}**
Last editor: **{data.updated_by}**
Updated at: `{data.updated_at}`
Changed by: **{actor.display_name}**
🔗 [Open newcomer guide]({resource.url})
        """
    ),
    'registration.request.approved': _message(
        """
✅ **Registration Approved**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Fleet application: `{data.wants_fleet_membership}`
Approved by: **{actor.display_name}** (`{actor.username}`)
Decision note: {data.decision_note}
Processed at: `{occurred_at}`
🔗 [Open registration management]({resource.url})
        """
    ),
    'registration.request.created': _message(
        """
🆕 **New Registration Request**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Fleet application: `{data.wants_fleet_membership}`
Fleet ID: `{data.fleet_id}`
Application note: {data.fleet_application_note}
Received at: `{occurred_at}`
🔗 [Review registration]({resource.url})
        """
    ),
    'registration.request.rejected': _message(
        """
⛔ **Registration Rejected**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Rejected by: **{actor.display_name}** (`{actor.username}`)
Decision note: {data.decision_note}
Processed at: `{occurred_at}`
🔗 [Open registration management]({resource.url})
        """
    ),
    'squad.archived': _message(
        """
📦 **Squad Archived**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Final member count: `{data.member_count}`
Archived by: **{actor.display_name}**
Archived at: `{occurred_at}`
🔗 [Open squad record]({resource.url})
        """
    ),
    'squad.created': _message(
        """
🛡️ **Squad Created**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Members: `{data.member_count}`
Created by: **{actor.display_name}**
Created at: `{occurred_at}`
🔗 [Open squad]({resource.url})
        """
    ),
    'squad.member.added': _message(
        """
➕ **Squad Member Added**
Squad: **{data.squad_name}**
Member: **{data.member_display_name}**
Role: `{data.member_role}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Added by: **{actor.display_name}**
Added at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
        """
    ),
    'squad.member.removed': _message(
        """
➖ **Squad Member Removed**
Squad: **{data.squad_name}**
Membership ID: `{data.member_id}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
        """
    ),
    'squad.member.updated': _message(
        """
🔄 **Squad Membership Updated**
Squad: **{data.squad_name}**
Membership ID: `{data.member_id}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Updated by: **{actor.display_name}**
Updated at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
        """
    ),
    'squad.updated': _message(
        """
🛠️ **Squad Updated**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Members: `{data.member_count}`
Updated by: **{actor.display_name}**
Updated at: `{occurred_at}`
🔗 [Open squad]({resource.url})
        """
    ),
}


DEFAULT_MESSAGES.update({
    'forum.thread.removed': _message(
        """
🗑️ **Forum Thread Removed**
Title: **{data.title}**
Thread ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse forum]({resource.url})
        """
    ),
    'forum.post.created': _message(
        """
💬 **New Forum Reply**
Thread ID: `{data.thread_id}`
Author: **{data.author.display_name}**
Reply ID: `{data.id}`
Posted at: `{data.created_at}`
Message: {data.body}
🔗 [Open discussion]({resource.url})
        """
    ),
    'forum.post.updated': _message(
        """
✏️ **Forum Reply Updated**
Thread ID: `{data.thread_id}`
Author: **{data.author.display_name}**
Reply ID: `{data.id}`
Updated by: **{actor.display_name}**
Updated at: `{data.updated_at}`
Message: {data.body}
🔗 [Open discussion]({resource.url})
        """
    ),
    'forum.post.removed': _message(
        """
🗑️ **Forum Reply Removed**
Thread ID: `{data.thread_id}`
Reply ID: `{data.id}`
Original author: **{data.author.display_name}**
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Open discussion]({resource.url})
        """
    ),
    'fleet.created': _message(
        """
⚓ **Fleet Created**
Fleet: **{data.name}**
Focus: `{data.focus}`
Members: `{data.active_members_count}`
Created by: **{actor.display_name}**
🔗 [Open fleet]({resource.url})
        """
    ),
    'fleet.updated': _message(
        """
🛠️ **Fleet Profile Updated**
Fleet: **{data.name}**
Focus: `{data.focus}`
Members: `{data.active_members_count}`
Description: {data.description}
Updated by: **{actor.display_name}**
🔗 [Open fleet]({resource.url})
        """
    ),
    'fleet.application.created': _message(
        """
📨 **New Fleet Application**
Applicant: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Status: `{data.status}`
Application note: {data.note}
🔗 [Open fleet management]({resource.url})
        """
    ),
    'fleet.membership.updated': _message(
        """
🧭 **Fleet Membership Updated**
Member: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Status: `{data.status}`
Role: `{data.role}`
Assignment: {data.assignment}
Updated by: **{actor.display_name}**
🔗 [Open fleet management]({resource.url})
        """
    ),
    'fleet.leader.assigned': _message(
        """
🧭 **Fleet Leadership Assigned**
Member: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Role: `{data.role}`
Assigned by: **{actor.display_name}**
🔗 [Open fleet management]({resource.url})
        """
    ),
    'fleet.role.created': _message(
        """
➕ **Fleet Role Created**
Role: **{data.label}** (`{data.code}`)
Rank: `{data.rank}`
Created by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
        """
    ),
    'fleet.role.updated': _message(
        """
🔄 **Fleet Role Updated**
Role: **{data.label}** (`{data.code}`)
Rank: `{data.rank}`
Active: `{data.is_active}`
Updated by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
        """
    ),
    'fleet.role.removed': _message(
        """
➖ **Fleet Role Removed**
Role: **{data.label}** (`{data.code}`)
Role ID: `{data.id}`
Removed by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
        """
    ),
})


__all__ = ["DEFAULT_MESSAGES"]
