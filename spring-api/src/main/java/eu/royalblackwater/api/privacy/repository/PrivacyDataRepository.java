package eu.royalblackwater.api.privacy.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the privacy domain. */
@Repository
public class PrivacyDataRepository extends JdbcRepositorySupport {
    public PrivacyDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
