package eu.royalblackwater.api.webhooks.service;

import eu.royalblackwater.api.audit.dto.AuditRecordedEvent;
import eu.royalblackwater.api.webhooks.dto.WebhookDomainEvent;
import java.util.Optional;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class WebhookAuditEventListener {
    private final WebhookService webhooks;

    public WebhookAuditEventListener(WebhookService webhooks) {
        this.webhooks = webhooks;
    }

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void deliver(AuditRecordedEvent audit) {
        map(audit).ifPresent(event -> {
            try {
                webhooks.publish(event);
            } catch (RuntimeException ignored) {
                // The audited operation is already committed; integrations are best effort.
            }
        });
    }

    static Optional<WebhookDomainEvent> map(AuditRecordedEvent audit) {
        String event = eventType(audit);
        if (event == null) return Optional.empty();
        return Optional.of(new WebhookDomainEvent(event, audit.entityType(), audit.entityId(),
                audit.scopeType(), audit.scopeId(), audit.actor(), audit.summary(), audit.occurredAt()));
    }

    private static String eventType(AuditRecordedEvent audit) {
        String key = audit.entityType() + ":" + audit.action();
        return switch (key) {
            case "build:create" -> "build.created";
            case "build:update" -> "build.updated";
            case "build:delete" -> "build.removed";
            case "build:printout_update" -> "build.printout.published";
            case "calendar_event:create" -> "calendar.event.created";
            case "calendar_event:update" -> "calendar.event.updated";
            case "calendar_event:cancel" -> "calendar.event.cancelled";
            case "fleet:create" -> "fleet.created";
            case "fleet:update" -> "fleet.updated";
            case "fleet_application:create" -> "fleet.application.created";
            case "fleet_role:create" -> "fleet.role.created";
            case "fleet_role:update" -> "fleet.role.updated";
            case "fleet_role:delete" -> "fleet.role.removed";
            case "forum_post:create" -> "forum.post.created";
            case "forum_post:update" -> "forum.post.updated";
            case "forum_post:delete" -> "forum.post.removed";
            case "forum_thread:create" -> "forum.thread.created";
            case "forum_thread:update" -> "forum.thread.updated";
            case "forum_thread:delete" -> "forum.thread.removed";
            case "group:create" -> "group.created";
            case "group:join" -> "group.member.joined";
            case "group:close" -> "group.closed";
            case "guide:create" -> "guide.created";
            case "guide:update" -> "guide.updated";
            case "guide:delete" -> "guide.removed";
            case "newcomer_guide:update" -> "newcomer_guide.updated";
            case "privacy_request:complete", "privacy_request:reject" -> "privacy.request.resolved";
            case "squad:create" -> "squad.created";
            case "squad:update" -> "squad.updated";
            case "squad:archive" -> "squad.archived";
            case "squad_member:create" -> "squad.member.added";
            case "squad_member:update" -> "squad.member.updated";
            case "squad_member:delete" -> "squad.member.removed";
            case "system_update:request" -> "system.update.started";
            case "privacy_request:create" -> "privacy.request.created";
            case "registration_request:create" -> "registration.request.created";
            default -> conditionalEvent(audit);
        };
    }

    private static String conditionalEvent(AuditRecordedEvent audit) {
        if ("registration_request".equals(audit.entityType()) && "update".equals(audit.action())) {
            return audit.summary().endsWith("approved.")
                    ? "registration.request.approved" : "registration.request.rejected";
        }
        if ("fleet_membership".equals(audit.entityType()) && "update".equals(audit.action())) {
            return audit.summary().startsWith("Assigned fleet leadership")
                    ? "fleet.leader.assigned" : "fleet.membership.updated";
        }
        if ("backup_control".equals(audit.entityType())) {
            if (audit.action().contains("restore")) return "backup.restore.requested";
            if (audit.action().contains("backup")) return "backup.run.requested";
            if (audit.action().contains("delete")) return "backup.configuration.deleted";
            if (audit.action().contains("prepared")) return "backup.configuration.updated";
        }
        return null;
    }

}
