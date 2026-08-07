package eu.royalblackwater.api.builds.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the builds domain. */
@Repository
public class BuildDataRepository extends JdbcRepositorySupport {
    public BuildDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
