package eu.royalblackwater.api.audit.service;

import eu.royalblackwater.api.audit.repository.AuditDataRepository;
import eu.royalblackwater.api.audit.repository.queries.AuditQueries;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Collection;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Service
public class AuditService {
    private final AuditDataRepository repository;
    private final ObjectMapper json;
    private final Clock clock;

    public AuditService(AuditDataRepository repository, ObjectMapper json, Clock clock) {
        this.repository = repository;
        this.json = json;
        this.clock = clock;
    }

    @Transactional
    public void record(AuthenticatedUser actor, String entityType, Object entityId, String action,
                       String summary, Collection<String> changedFields) {
        List<String> fields = changedFields == null ? List.of() : changedFields.stream()
                .filter(value -> value != null && !value.isBlank()).map(String::strip).distinct().sorted().toList();
        repository.update(AuditQueries.RECORD_INSERT_01, SqlParameters.ofNullable(
                        "createdAt", LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC),
                        "actorId", actor.id(),
                        "username", actor.username(),
                        "role", actor.role(),
                        "entityType", entityType,
                        "entityId", String.valueOf(entityId),
                        "action", action,
                        "summary", summary.length() > 500 ? summary.substring(0, 500) : summary,
                        "changedFields", fields.isEmpty() ? null : writeJson(fields)));
    }

    private String writeJson(List<String> fields) {
        try {
            return json.writeValueAsString(fields);
        } catch (JacksonException exception) {
            throw new IllegalStateException("Could not serialize audit metadata.", exception);
        }
    }
}
