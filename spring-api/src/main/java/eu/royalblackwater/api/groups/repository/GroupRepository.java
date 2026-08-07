package eu.royalblackwater.api.groups.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the groups domain. */
@Repository
public class GroupRepository extends JdbcRepositorySupport {
    public GroupRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
