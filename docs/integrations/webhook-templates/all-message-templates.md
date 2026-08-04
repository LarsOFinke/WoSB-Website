# Discord webhook message templates

Generated from `contracts/webhook-events.json`.

## `backup.configuration.deleted`

The protected backup connection configuration was removed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `backup.configuration.updated`

The protected backup connection configuration changed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `backup.restore.requested`

A bootstrap administrator requested a database restore.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `backup.run.requested`

An administrator requested a protected application backup.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `build.created`

A new build was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `build.printout.published`

A public build printout was published to Discord.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `build.removed`

A build was removed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `build.updated`

A build was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `calendar.event.cancelled`

A fleet or squad event was cancelled.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `calendar.event.created`

A fleet or squad event was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `calendar.event.updated`

A fleet or squad event was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.application.created`

A fleet application was submitted.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.created`

A fleet was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.leader.assigned`

A fleet leadership role was assigned.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.membership.updated`

A fleet membership was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.role.created`

A fleet role was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.role.removed`

A fleet role was removed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.role.updated`

A fleet role was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `fleet.updated`

A fleet profile was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.post.created`

A new forum reply was posted.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.post.removed`

A forum reply was removed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.post.updated`

A forum reply was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.thread.created`

A new forum thread was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.thread.removed`

A forum thread was removed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `forum.thread.updated`

A forum thread was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `group.closed`

A group-search listing was closed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `group.created`

A new group-search listing was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `group.member.joined`

A member joined a group-search listing.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `guide.created`

A new guide was published.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `guide.removed`

A guide was removed from publication.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `guide.updated`

A published guide was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `integration.test`

Manual connectivity and payload test.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `newcomer_guide.updated`

The starter guide was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `privacy.request.created`

A data-subject request requires an administrator response.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `privacy.request.resolved`

A data-subject request was resolved by an administrator.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `registration.request.approved`

An access request was approved.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `registration.request.created`

A new access request was submitted.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `registration.request.rejected`

An access request was rejected.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.archived`

A squad was archived.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.created`

A squad was created.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.member.added`

A member was added to a squad.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.member.removed`

A member was removed from a squad.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.member.updated`

A squad membership was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `squad.updated`

A squad was updated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `system.maintenance.ended`

A maintenance window ended or failed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `system.maintenance.started`

A maintenance window was activated.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `system.update.result`

A controlled server operation completed or failed.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```

## `system.update.started`

A controlled server operation was requested and queued.

```text
RBF event **{event}** for {resource.type} #{resource.id}.
```
