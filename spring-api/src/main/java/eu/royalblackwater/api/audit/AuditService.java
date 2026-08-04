package eu.royalblackwater.api.audit;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
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
    private final JdbcQueryService jdbc;
    private final ObjectMapper json;
    private final Clock clock;

    public AuditService(JdbcQueryService jdbc, ObjectMapper json, Clock clock) {
        this.jdbc = jdbc;
        this.json = json;
        this.clock = clock;
    }

    @Transactional
    public void record(AuthenticatedUser actor, String entityType, Object entityId, String action,
                       String summary, Collection<String> changedFields) {
        List<String> fields = changedFields == null ? List.of() : changedFields.stream()
                .filter(value -> value != null && !value.isBlank()).map(String::strip).distinct().sorted().toList();
        jdbc.update("""
                insert into audit_logs
                    (created_at, actor_user_id, actor_username, actor_role, entity_type,
                     entity_id, action, summary, changed_fields_json)
                values (:createdAt, :actorId, :username, :role, :entityType,
                        :entityId, :action, :summary, :changedFields)
                """, SqlParameters.ofNullable(
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
