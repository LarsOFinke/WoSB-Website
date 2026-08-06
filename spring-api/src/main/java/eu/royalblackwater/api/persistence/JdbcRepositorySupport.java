package eu.royalblackwater.api.persistence;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Shared JDBC mechanics for module-owned repositories. Domain services must depend on a
 * repository in their own module and never on the generic JDBC executor directly.
 */
public abstract class JdbcRepositorySupport {
    private final JdbcQueryService jdbc;

    protected JdbcRepositorySupport(JdbcQueryService jdbc) {
        this.jdbc = jdbc;
    }

    public final List<Map<String, Object>> query(String sql, Map<String, ?> parameters) {
        return jdbc.query(sql, parameters);
    }

    public final Optional<Map<String, Object>> optional(String sql, Map<String, ?> parameters) {
        return jdbc.optional(sql, parameters);
    }

    public final Map<String, Object> required(String sql, Map<String, ?> parameters) {
        return jdbc.required(sql, parameters);
    }

    public final int update(String sql, Map<String, ?> parameters) {
        return jdbc.update(sql, parameters);
    }

    public final long insertReturningId(String sql, Map<String, ?> parameters) {
        return jdbc.insertReturningId(sql, parameters);
    }

    public final long count(String sql, Map<String, ?> parameters) {
        return jdbc.count(sql, parameters);
    }
}
