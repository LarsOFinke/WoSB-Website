package eu.royalblackwater.api.core.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.util.Map;
import org.springframework.stereotype.Repository;

@Repository
public class CoreRepository {
    private final JdbcQueryService jdbc;

    public CoreRepository(JdbcQueryService jdbc) {
        this.jdbc = jdbc;
    }

    public void verifyDatabaseConnection() {
        jdbc.count("select 1", Map.of());
    }
}
