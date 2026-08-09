# Discord webhook message templates

Generated from `spring-api/src/main/reference/webhook-events.json`.

This is the single copy-ready reference. Runtime defaults and the staff-panel autofill are derived from the same event catalog.

## Builds

### `build.created`

A new build was created.

```text
🧰 **A new build was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `build.printout.published`

A public build printout was published to Discord.

```text
🧰 **A public build printout was published to Discord**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `build.removed`

A build was removed.

```text
🧰 **A build was removed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `build.updated`

A build was updated.

```text
🧰 **A build was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Calendar

### `calendar.event.cancelled`

A fleet or squad event was cancelled.

```text
📅 **A fleet or squad event was cancelled**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `calendar.event.created`

A fleet or squad event was created.

```text
📅 **A fleet or squad event was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `calendar.event.updated`

A fleet or squad event was updated.

```text
📅 **A fleet or squad event was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Content

### `guide.created`

A new guide was published.

```text
📘 **A new guide was published**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `guide.removed`

A guide was removed from publication.

```text
📘 **A guide was removed from publication**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `guide.updated`

A published guide was updated.

```text
📘 **A published guide was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `newcomer_guide.updated`

The starter guide was updated.

```text
📘 **The starter guide was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Fleet

### `fleet.application.created`

A fleet application was submitted.

```text
🏴‍☠️ **A fleet application was submitted**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.created`

A fleet was created.

```text
🏴‍☠️ **A fleet was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.leader.assigned`

A fleet leadership role was assigned.

```text
🏴‍☠️ **A fleet leadership role was assigned**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.membership.updated`

A fleet membership was updated.

```text
🏴‍☠️ **A fleet membership was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.role.created`

A fleet role was created.

```text
🏴‍☠️ **A fleet role was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.role.removed`

A fleet role was removed.

```text
🏴‍☠️ **A fleet role was removed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.role.updated`

A fleet role was updated.

```text
🏴‍☠️ **A fleet role was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `fleet.updated`

A fleet profile was updated.

```text
🏴‍☠️ **A fleet profile was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Forum

### `forum.post.created`

A new forum reply was posted.

```text
💬 **A new forum reply was posted**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `forum.post.removed`

A forum reply was removed.

```text
💬 **A forum reply was removed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `forum.post.updated`

A forum reply was updated.

```text
💬 **A forum reply was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `forum.thread.created`

A new forum thread was created.

```text
💬 **A new forum thread was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `forum.thread.removed`

A forum thread was removed.

```text
💬 **A forum thread was removed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `forum.thread.updated`

A forum thread was updated.

```text
💬 **A forum thread was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Groups

### `group.closed`

A group-search listing was closed.

```text
🔎 **A group-search listing was closed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `group.created`

A new group-search listing was created.

```text
🔎 **A new group-search listing was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `group.member.joined`

A member joined a group-search listing.

```text
🔎 **A member joined a group-search listing**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Integration

### `integration.test`

Manual connectivity and payload test.

```text
🧪 **Manual connectivity and payload test**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Moderation

### `privacy.request.created`

A data-subject request requires an administrator response.

```text
🛡️ **A data-subject request requires an administrator response**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `privacy.request.resolved`

A data-subject request was resolved by an administrator.

```text
🛡️ **A data-subject request was resolved by an administrator**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Operations

### `backup.configuration.deleted`

The protected backup connection configuration was removed.

```text
💾 **The protected backup connection configuration was removed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `backup.configuration.updated`

The protected backup connection configuration changed.

```text
💾 **The protected backup connection configuration changed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `backup.restore.requested`

A bootstrap administrator requested a database restore.

```text
💾 **A bootstrap administrator requested a database restore**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `backup.run.requested`

An administrator requested a protected application backup.

```text
💾 **An administrator requested a protected application backup**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Registrations

### `registration.request.approved`

An access request was approved.

```text
🔔 **An access request was approved**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `registration.request.created`

A new access request was submitted.

```text
🔔 **A new access request was submitted**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `registration.request.rejected`

An access request was rejected.

```text
🔔 **An access request was rejected**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## Squads

### `squad.archived`

A squad was archived.

```text
⚓ **A squad was archived**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `squad.created`

A squad was created.

```text
⚓ **A squad was created**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `squad.member.added`

A member was added to a squad.

```text
⚓ **A member was added to a squad**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `squad.member.removed`

A member was removed from a squad.

```text
⚓ **A member was removed from a squad**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `squad.member.updated`

A squad membership was updated.

```text
⚓ **A squad membership was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `squad.updated`

A squad was updated.

```text
⚓ **A squad was updated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

## System

### `system.maintenance.ended`

A maintenance window ended or failed.

```text
🛠️ **A maintenance window ended or failed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `system.maintenance.started`

A maintenance window was activated.

```text
🛠️ **A maintenance window was activated**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `system.update.result`

A controlled server operation completed or failed.

```text
🛠️ **A controlled server operation completed or failed**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```

### `system.update.started`

A controlled server operation was requested and queued.

```text
🛠️ **A controlled server operation was requested and queued**

{data.summary}

Resource: `{resource.type} #{resource.id}`
Event: `{event}`
Triggered by **{actor.display_name}** at `{occurred_at}`.
```
