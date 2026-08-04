package eu.royalblackwater.api.audit;

import eu.royalblackwater.api.contract.AuditLogRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;
import static org.springframework.http.HttpStatus.BAD_REQUEST;

@Service
public class AuditLogQueryService {
    private final JdbcQueryService jdbc;
    private final ObjectMapper json;

    public AuditLogQueryService(JdbcQueryService jdbc, ObjectMapper json) {
        this.jdbc = jdbc;
        this.json = json;
    }

    @Transactional(readOnly = true)
    public List<AuditLogRead> list(String entityType, String action, String actor,
                                   LocalDate fromDate, LocalDate toDate, long limit) {
        if (limit < 1 || limit > 500) throw new ResponseStatusException(BAD_REQUEST, "limit must be between 1 and 500.");
        if (fromDate != null && toDate != null && toDate.isBefore(fromDate)) {
            throw new ResponseStatusException(BAD_REQUEST, "to_date must not be before from_date.");
        }
        StringBuilder sql = new StringBuilder("select * from audit_logs where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        appendExact(sql, parameters, "entity_type", "entityType", entityType);
        appendExact(sql, parameters, "action", "action", action);
        if (actor != null && !actor.isBlank()) {
            sql.append(" and actor_username ilike :actor");
            parameters.put("actor", "%" + actor.strip() + "%");
        }
        if (fromDate != null) {
            sql.append(" and created_at>=:fromDate");
            parameters.put("fromDate", LocalDateTime.of(fromDate, LocalTime.MIN));
        }
        if (toDate != null) {
            sql.append(" and created_at<:toDate");
            parameters.put("toDate", LocalDateTime.of(toDate.plusDays(1), LocalTime.MIN));
        }
        sql.append(" order by created_at desc,id desc limit :limit");
        parameters.put("limit", limit);
        return jdbc.query(sql.toString(), parameters).stream().map(this::read).toList();
    }

    private AuditLogRead read(Map<String, Object> row) {
        return new AuditLogRead(RowValues.requiredString(row,"action"),RowValues.requiredString(row,"actor_role"),
                RowValues.nullableLong(row,"actor_user_id"),RowValues.requiredString(row,"actor_username"),
                changedFields(RowValues.string(row,"changed_fields_json")),RowValues.dateTime(row,"created_at"),
                RowValues.requiredString(row,"entity_id"),RowValues.requiredString(row,"entity_type"),
                RowValues.longValue(row,"id"),RowValues.requiredString(row,"summary"));
    }

    private List<String> changedFields(String raw) {
        if (raw == null || raw.isBlank()) return List.of();
        try {
            Object decoded = json.readValue(raw, Object.class);
            if (!(decoded instanceof List<?> values)) return List.of();
            List<String> result = new ArrayList<>();
            for (Object value : values) {
                if (value instanceof String text && !text.isBlank()) result.add(text);
            }
            return List.copyOf(result);
        } catch (JacksonException exception) {
            return List.of();
        }
    }

    private static void appendExact(StringBuilder sql, Map<String, Object> parameters,
                                    String column, String parameter, String value) {
        if (value == null || value.isBlank()) return;
        sql.append(" and ").append(column).append("=:").append(parameter);
        parameters.put(parameter, value.strip());
    }
}
