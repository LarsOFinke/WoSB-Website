package eu.royalblackwater.api.audit.service;

import eu.royalblackwater.api.audit.dto.AuditRecordedEvent;
import eu.royalblackwater.api.audit.repository.AuditDataRepository;
import eu.royalblackwater.api.audit.repository.queries.AuditQueries;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Collection;
import java.util.List;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Service
public class AuditService {
    private final AuditDataRepository repository;
    private final ObjectMapper json;
    private final Clock clock;
    private final ApplicationEventPublisher events;

    public AuditService(AuditDataRepository repository, ObjectMapper json, Clock clock,
                        ApplicationEventPublisher events) {
        this.repository = repository;
        this.json = json;
        this.clock = clock;
        this.events = events;
    }

    @Transactional
    public void record(AuthenticatedUser actor, String entityType, Object entityId, String action,
                       String summary, Collection<String> changedFields) {
        String scopeType = Set.of("fleet", "squad").contains(entityType) ? entityType : null;
        Long scopeId = scopeType == null ? null : numericId(entityId);
        record(actor, entityType, entityId, action, summary, changedFields, scopeType, scopeId);
    }

    @Transactional
    public void record(AuthenticatedUser actor, String entityType, Object entityId, String action,
                       String summary, Collection<String> changedFields, String scopeType, Long scopeId) {
        List<String> fields = changedFields == null ? List.of() : changedFields.stream()
                .filter(value -> value != null && !value.isBlank()).map(String::strip).distinct().sorted().toList();
        LocalDateTime createdAt = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        String entityIdentifier = String.valueOf(entityId);
        repository.update(AuditQueries.RECORD_INSERT_01, SqlParameters.ofNullable(
                        "createdAt", createdAt,
                        "actorId", actor == null ? null : actor.id(),
                        "username", actor == null ? "RBF system" : actor.username(),
                        "role", actor == null ? "system" : actor.role(),
                        "entityType", entityType,
                        "entityId", entityIdentifier,
                        "action", action,
                        "summary", summary.length() > 500 ? summary.substring(0, 500) : summary,
                        "changedFields", fields.isEmpty() ? null : writeJson(fields)));
        events.publishEvent(new AuditRecordedEvent(
                action, actor, entityIdentifier, entityType, createdAt, scopeId, scopeType, summary));
    }

    private static Long numericId(Object value) {
        try {
            return Long.valueOf(String.valueOf(value));
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private String writeJson(List<String> fields) {
        try {
            return json.writeValueAsString(fields);
        } catch (JacksonException exception) {
            throw new IllegalStateException("Could not serialize audit metadata.", exception);
        }
    }
}
