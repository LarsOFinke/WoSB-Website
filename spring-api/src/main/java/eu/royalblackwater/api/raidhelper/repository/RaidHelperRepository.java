package eu.royalblackwater.api.raidhelper.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the raidhelper domain. */
@Repository
public class RaidHelperRepository extends JdbcRepositorySupport {
    public RaidHelperRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
