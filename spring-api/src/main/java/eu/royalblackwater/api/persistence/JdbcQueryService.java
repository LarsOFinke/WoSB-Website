package eu.royalblackwater.api.persistence;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class JdbcQueryService {
    private final NamedParameterJdbcTemplate jdbc;

    public JdbcQueryService(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> query(String sql, Map<String, ?> parameters) {
        return jdbc.queryForList(sql, parameters);
    }

    public Optional<Map<String, Object>> optional(String sql, Map<String, ?> parameters) {
        List<Map<String, Object>> rows = query(sql, parameters);
        if (rows.size() > 1) {
            throw new IllegalStateException("Expected at most one row but received " + rows.size());
        }
        return rows.stream().findFirst();
    }

    public Map<String, Object> required(String sql, Map<String, ?> parameters) {
        return optional(sql, parameters).orElseThrow();
    }

    public int update(String sql, Map<String, ?> parameters) {
        return jdbc.update(sql, parameters);
    }

    public long insertReturningId(String sql, Map<String, ?> parameters) {
        MapSqlParameterSource source = new MapSqlParameterSource();
        parameters.forEach(source::addValue);
        Number id = jdbc.queryForObject(sql, source, Number.class);
        if (id == null) {
            throw new IllegalStateException("Insert did not return an identifier.");
        }
        return id.longValue();
    }

    public long count(String sql, Map<String, ?> parameters) {
        Long value = jdbc.queryForObject(sql, parameters, Long.class);
        return value == null ? 0 : value;
    }
}
