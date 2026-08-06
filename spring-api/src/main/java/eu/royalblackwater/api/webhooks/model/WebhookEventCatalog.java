package eu.royalblackwater.api.webhooks.model;

import eu.royalblackwater.api.dto.OutboundWebhookEventCatalogItem;
import java.util.List;
import java.util.Set;

public final class WebhookEventCatalog {
    public static final List<OutboundWebhookEventCatalogItem> ALL = List.of(
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "Manual connectivity and payload test.", "integration", "integration.test"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A controlled server operation was requested and queued.", "system", "system.update.started"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A controlled server operation completed or failed.", "system", "system.update.result"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A maintenance window was activated.", "system", "system.maintenance.started"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A maintenance window ended or failed.", "system", "system.maintenance.ended"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "An administrator requested a protected application backup.", "operations", "backup.run.requested"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A bootstrap administrator requested a database restore.", "operations", "backup.restore.requested"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "The protected backup connection configuration changed.", "operations", "backup.configuration.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "The protected backup connection configuration was removed.", "operations", "backup.configuration.deleted"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A data-subject request requires an administrator response.", "moderation", "privacy.request.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A data-subject request was resolved by an administrator.", "moderation", "privacy.request.resolved"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new access request was submitted.", "registrations", "registration.request.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "An access request was approved.", "registrations", "registration.request.approved"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "An access request was rejected.", "registrations", "registration.request.rejected"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A squad was created.", "squads", "squad.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A squad was updated.", "squads", "squad.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A squad was archived.", "squads", "squad.archived"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A member was added to a squad.", "squads", "squad.member.added"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A squad membership was updated.", "squads", "squad.member.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A member was removed from a squad.", "squads", "squad.member.removed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new group-search listing was created.", "groups", "group.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A member joined a group-search listing.", "groups", "group.member.joined"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A group-search listing was closed.", "groups", "group.closed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet or squad event was created.", "calendar", "calendar.event.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet or squad event was updated.", "calendar", "calendar.event.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet or squad event was cancelled.", "calendar", "calendar.event.cancelled"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new guide was published.", "content", "guide.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A published guide was updated.", "content", "guide.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A guide was removed from publication.", "content", "guide.removed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "The starter guide was updated.", "content", "newcomer_guide.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new build was created.", "builds", "build.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A build was updated.", "builds", "build.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A build was removed.", "builds", "build.removed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A public build printout was published to Discord.", "builds", "build.printout.published"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new forum thread was created.", "forum", "forum.thread.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A forum thread was updated.", "forum", "forum.thread.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A forum thread was removed.", "forum", "forum.thread.removed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A new forum reply was posted.", "forum", "forum.post.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A forum reply was updated.", "forum", "forum.post.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A forum reply was removed.", "forum", "forum.post.removed"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet was created.", "fleet", "fleet.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet profile was updated.", "fleet", "fleet.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet application was submitted.", "fleet", "fleet.application.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet membership was updated.", "fleet", "fleet.membership.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet leadership role was assigned.", "fleet", "fleet.leader.assigned"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet role was created.", "fleet", "fleet.role.created"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet role was updated.", "fleet", "fleet.role.updated"),
            new OutboundWebhookEventCatalogItem("RBF event **{event}** for {resource.type} #{resource.id}.", "A fleet role was removed.", "fleet", "fleet.role.removed")
    );
    public static final Set<String> TYPES = ALL.stream().map(OutboundWebhookEventCatalogItem::key).collect(java.util.stream.Collectors.toUnmodifiableSet());

    private WebhookEventCatalog() { }
}
