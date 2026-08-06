package eu.royalblackwater.api.forum.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the forum domain. */
@Repository
public final class ForumRepository extends JdbcRepositorySupport {
    public ForumRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
