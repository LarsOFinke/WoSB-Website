# Discord webhook message templates

Generated from the versioned backend defaults. Use the Staff Panel presets for
moderation, operations or public calendar channels and customize only when needed.

## `backup.configuration.deleted`

```text
🔐 **Backup Configuration Removed**
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Reference: `{resource.id}`
🔗 [Open backup administration]({resource.url})
```

## `backup.configuration.updated`

```text
🔐 **Backup Configuration Changed**
Action: `{data.action}`
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Reference: `{resource.id}`
🔗 [Open backup administration]({resource.url})
```

## `backup.restore.requested`

```text
🚨 **Database Restore Requested**
Backup reference: `{data.backup_id}`
Requested by: **{actor.display_name}**
Status: awaiting protected host approval
🔗 [Review backup status]({resource.url})
```

## `backup.run.requested`

```text
💾 **Application Backup Requested**
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Includes: database, uploads and encrypted recovery bundle
🔗 [Review backup status]({resource.url})
```

## `build.created`

```text
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
```

## `build.removed`

```text
🗑️ **Build Removed**
Build: **{data.build_name}**
Build ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse remaining builds]({resource.url})
```

## `build.updated`

```text
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
```

## `calendar.event.cancelled`

```text
❌ **Shoutout cancelled: {data.title}**
The calendar event scheduled for `{data.start_at}` will not take place.
📍 {data.location}
🔗 [See the current calendar]({resource.url})
```

## `calendar.event.created`

```text
🏴‍☠️ **Fleet shoutout: {data.title}**
🗓️ Starts: `{data.start_at}`
⏱️ Ends: `{data.end_at}`
📍 {data.location}
👥 Hosted by **{data.owner.display_name}** for **{data.scope_name}**
🔗 [Open event and join in]({resource.url})
```

## `calendar.event.updated`

```text
📣 **Shoutout updated: {data.title}**
🗓️ Starts: `{data.start_at}` · Ends: `{data.end_at}`
📍 {data.location}
👥 Hosted by **{data.owner.display_name}** for **{data.scope_name}**
🔗 [Check the latest event details]({resource.url})
```

## `fleet.application.created`

```text
📨 **New Fleet Application**
Applicant: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Status: `{data.status}`
Application note: {data.note}
🔗 [Open fleet management]({resource.url})
```

## `fleet.created`

```text
⚓ **Fleet Created**
Fleet: **{data.name}**
Focus: `{data.focus}`
Members: `{data.active_members_count}`
Created by: **{actor.display_name}**
🔗 [Open fleet]({resource.url})
```

## `fleet.leader.assigned`

```text
🧭 **Fleet Leadership Assigned**
Member: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Role: `{data.role}`
Assigned by: **{actor.display_name}**
🔗 [Open fleet management]({resource.url})
```

## `fleet.membership.updated`

```text
🧭 **Fleet Membership Updated**
Member: **{data.user.display_name}** (`{data.user.username}`)
Fleet ID: `{data.fleet_id}`
Status: `{data.status}`
Role: `{data.role}`
Assignment: {data.assignment}
Updated by: **{actor.display_name}**
🔗 [Open fleet management]({resource.url})
```

## `fleet.role.created`

```text
➕ **Fleet Role Created**
Role: **{data.label}** (`{data.code}`)
Rank: `{data.rank}`
Created by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
```

## `fleet.role.removed`

```text
➖ **Fleet Role Removed**
Role: **{data.label}** (`{data.code}`)
Role ID: `{data.id}`
Removed by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
```

## `fleet.role.updated`

```text
🔄 **Fleet Role Updated**
Role: **{data.label}** (`{data.code}`)
Rank: `{data.rank}`
Active: `{data.is_active}`
Updated by: **{actor.display_name}**
🔗 [Open fleet roles]({resource.url})
```

## `fleet.updated`

```text
🛠️ **Fleet Profile Updated**
Fleet: **{data.name}**
Focus: `{data.focus}`
Members: `{data.active_members_count}`
Description: {data.description}
Updated by: **{actor.display_name}**
🔗 [Open fleet]({resource.url})
```

## `forum.post.created`

```text
💬 **New Forum Reply**
Thread ID: `{data.thread_id}`
Author: **{data.author.display_name}**
Reply ID: `{data.id}`
Posted at: `{data.created_at}`
Message: {data.body}
🔗 [Open discussion]({resource.url})
```

## `forum.post.removed`

```text
🗑️ **Forum Reply Removed**
Thread ID: `{data.thread_id}`
Reply ID: `{data.id}`
Original author: **{data.author.display_name}**
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Open discussion]({resource.url})
```

## `forum.post.updated`

```text
✏️ **Forum Reply Updated**
Thread ID: `{data.thread_id}`
Author: **{data.author.display_name}**
Reply ID: `{data.id}`
Updated by: **{actor.display_name}**
Updated at: `{data.updated_at}`
Message: {data.body}
🔗 [Open discussion]({resource.url})
```

## `forum.thread.created`

```text
💬 **New Forum Thread**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Replies: `{data.reply_count}`
Created at: `{data.created_at}`
Last activity: `{data.last_activity_at}`
Created by: **{actor.display_name}**
🔗 [Open thread]({resource.url})
```

## `forum.thread.removed`

```text
🗑️ **Forum Thread Removed**
Title: **{data.title}**
Thread ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse forum]({resource.url})
```

## `forum.thread.updated`

```text
✏️ **Forum Thread Updated**
Title: **{data.title}**
Category: `{data.category}`
Author: **{data.owner.display_name}**
Replies: `{data.reply_count}`
Last activity: `{data.last_activity_at}`
Updated by: **{actor.display_name}**
Updated at: `{data.updated_at}`
🔗 [Open thread]({resource.url})
```

## `group.closed`

```text
🔒 **Group Search Closed**
Group: **{data.title}**
Focus: `{data.focus}`
Members: `{data.active_members_count}` / `{data.max_members}`
Closed by: **{actor.display_name}**
Closed at: `{occurred_at}`
🔗 [Open group record]({resource.url})
```

## `group.created`

```text
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
```

## `group.member.joined`

```text
🙋 **Member Joined Group Search**
Group: **{data.title}**
Member: **{data.member.display_name}**
Fleet: {data.member.fleet_name}
Ship: **{data.member.ship_name}** (Rate `{data.member.ship_rate}`)
Members: `{data.active_members_count}` / `{data.max_members}`
Remaining slots: `{data.spots_left}`
Joined at: `{occurred_at}`
🔗 [Open group search]({resource.url})
```

## `guide.created`

```text
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
```

## `guide.removed`

```text
🗑️ **Guide Removed**
Title: **{data.title}**
Guide ID: `{data.id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Browse remaining guides]({resource.url})
```

## `guide.updated`

```text
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
```

## `integration.test`

```text
🧪 **RBF Webhook Test**
Destination: **{destination.name}**
Event: `{event}`
Delivery ID: `{id}`
Occurred at: `{occurred_at}`
Message: {data.message}
```

## `newcomer_guide.updated`

```text
🧭 **Newcomer Guide Updated**
Title: **{data.title}**
Last editor: **{data.updated_by}**
Updated at: `{data.updated_at}`
Changed by: **{actor.display_name}**
🔗 [Open newcomer guide]({resource.url})
```

## `privacy.request.created`

```text
🛡️ **Data-Subject Request Needs Review**
Type: `{data.request_type}`
Request ID: `{data.id}`
Submitted at: `{occurred_at}`
No request details are sent to Discord.
👉 [Open the protected privacy queue]({resource.url})
```

## `privacy.request.resolved`

```text
✅ **Data-Subject Request Resolved**
Type: `{data.request_type}`
Request ID: `{data.id}`
Decision: `{data.decision}`
Resolved by: **{actor.display_name}**
No resolution details are sent to Discord.
🔗 [Open privacy administration]({resource.url})
```

## `registration.request.approved`

```text
✅ **Registration Approved**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Fleet application: `{data.wants_fleet_membership}`
Approved by: **{actor.display_name}** (`{actor.username}`)
Decision note: {data.decision_note}
Processed at: `{occurred_at}`
🔗 [Open registration management]({resource.url})
```

## `registration.request.created`

```text
🔔 **Registration Needs Review**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Fleet application: `{data.wants_fleet_membership}`
Received at: `{occurred_at}`
👉 **Please review promptly:** [Open moderation queue]({resource.url})
```

## `registration.request.rejected`

```text
⛔ **Registration Rejected**
Name: **{data.display_name}**
Username: `{data.username}`
Request ID: `{data.id}`
Rejected by: **{actor.display_name}** (`{actor.username}`)
Decision note: {data.decision_note}
Processed at: `{occurred_at}`
🔗 [Open registration management]({resource.url})
```

## `squad.archived`

```text
📦 **Squad Archived**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Final member count: `{data.member_count}`
Archived by: **{actor.display_name}**
Archived at: `{occurred_at}`
🔗 [Open squad record]({resource.url})
```

## `squad.created`

```text
🛡️ **Squad Created**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Members: `{data.member_count}`
Created by: **{actor.display_name}**
Created at: `{occurred_at}`
🔗 [Open squad]({resource.url})
```

## `squad.member.added`

```text
➕ **Squad Member Added**
Squad: **{data.squad_name}**
Member: **{data.member_display_name}**
Role: `{data.member_role}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Added by: **{actor.display_name}**
Added at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
```

## `squad.member.removed`

```text
➖ **Squad Member Removed**
Squad: **{data.squad_name}**
Membership ID: `{data.member_id}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Removed by: **{actor.display_name}**
Removed at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
```

## `squad.member.updated`

```text
🔄 **Squad Membership Updated**
Squad: **{data.squad_name}**
Membership ID: `{data.member_id}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Updated by: **{actor.display_name}**
Updated at: `{occurred_at}`
🔗 [Open squad roster]({resource.url})
```

## `squad.updated`

```text
🛠️ **Squad Updated**
Name: **{data.name}**
Slug: `{data.slug}`
Squad ID: `{data.id}`
Fleet ID: `{data.fleet_id}`
Members: `{data.member_count}`
Updated by: **{actor.display_name}**
Updated at: `{occurred_at}`
🔗 [Open squad]({resource.url})
```

## `system.update.result`

```text
{data.state} **Server Operation Result**
Mode: `{data.operation}`
Result: `{data.state}`
Requested by: **{data.requested_by}**
Started: `{data.started_at}`
Finished: `{data.finished_at}`
Revision: `{data.commit_before}` → `{data.commit_after}`
{data.message}
🔗 [Open system status]({resource.url})
```

## `system.update.started`

```text
🚀 **Server Operation Started**
Mode: `{data.operation}`
Requested by: **{data.requested_by}**
Requested at: `{data.requested_at}`
Status: `{data.state}`
{data.message}
🔗 [Open system status]({resource.url})
```
