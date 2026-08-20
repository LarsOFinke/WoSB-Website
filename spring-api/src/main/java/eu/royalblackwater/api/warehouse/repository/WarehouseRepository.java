package eu.royalblackwater.api.warehouse.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for guild warehouse state. */
@Repository
public class WarehouseRepository extends JdbcRepositorySupport {
    public WarehouseRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
