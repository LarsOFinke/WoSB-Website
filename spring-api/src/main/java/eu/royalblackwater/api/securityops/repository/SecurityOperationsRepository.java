package eu.royalblackwater.api.securityops.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the securityops domain. */
@Repository
public final class SecurityOperationsRepository extends JdbcRepositorySupport {
    public SecurityOperationsRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
