package eu.royalblackwater.api.onboarding.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the onboarding domain. */
@Repository
public final class NewcomerGuideRepository extends JdbcRepositorySupport {
    public NewcomerGuideRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
