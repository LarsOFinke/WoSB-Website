package eu.royalblackwater.api.squads.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the squads domain. */
@Repository
public final class SquadRepository extends JdbcRepositorySupport {
    public SquadRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
