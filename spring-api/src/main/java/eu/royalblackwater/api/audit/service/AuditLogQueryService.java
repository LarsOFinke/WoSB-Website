package eu.royalblackwater.api.audit.service;

import eu.royalblackwater.api.audit.mapper.AuditDtoMapper;
import eu.royalblackwater.api.audit.repository.AuditDataRepository;
import eu.royalblackwater.api.audit.repository.queries.AuditLogQueryQueries;
import eu.royalblackwater.api.dto.AuditLogRead;
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
    private final AuditDataRepository repository;
    private final ObjectMapper json;

    public AuditLogQueryService(AuditDataRepository repository, ObjectMapper json) {
        this.repository = repository;
        this.json = json;
    }

    @Transactional(readOnly = true)
    public List<AuditLogRead> list(String entityType, String action, String actor,
                                   LocalDate fromDate, LocalDate toDate, long limit) {
        if (limit < 1 || limit > 500) throw new ResponseStatusException(BAD_REQUEST, AuditLogQueryQueries.LIST_SQL_01);
        if (fromDate != null && toDate != null && toDate.isBefore(fromDate)) {
            throw new ResponseStatusException(BAD_REQUEST, "to_date must not be before from_date.");
        }
        StringBuilder sql = new StringBuilder(AuditLogQueryQueries.LIST_SELECT_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        appendExact(sql, parameters, "entity_type", "entityType", entityType);
        appendExact(sql, parameters, "action", "action", action);
        if (actor != null && !actor.isBlank()) {
            sql.append(AuditLogQueryQueries.LIST_AND_01);
            parameters.put("actor", "%" + actor.strip() + "%");
        }
        if (fromDate != null) {
            sql.append(AuditLogQueryQueries.LIST_AND_02);
            parameters.put("fromDate", LocalDateTime.of(fromDate, LocalTime.MIN));
        }
        if (toDate != null) {
            sql.append(AuditLogQueryQueries.LIST_AND_03);
            parameters.put("toDate", LocalDateTime.of(toDate.plusDays(1), LocalTime.MIN));
        }
        sql.append(AuditLogQueryQueries.LIST_ORDER_BY_01);
        parameters.put("limit", limit);
        return repository.query(sql.toString(), parameters).stream()
                .map(row -> AuditDtoMapper.toRead(row, changedFields(RowValues.string(row, "changed_fields_json"))))
                .toList();
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
