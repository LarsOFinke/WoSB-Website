package eu.royalblackwater.api.guides.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the guides domain. */
@Repository
public class GuideRepository extends JdbcRepositorySupport {
    public GuideRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
