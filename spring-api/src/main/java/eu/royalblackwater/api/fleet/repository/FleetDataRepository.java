package eu.royalblackwater.api.fleet.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the fleet domain. */
@Repository
public final class FleetDataRepository extends JdbcRepositorySupport {
    public FleetDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
