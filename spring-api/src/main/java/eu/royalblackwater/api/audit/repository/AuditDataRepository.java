package eu.royalblackwater.api.audit.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the audit domain. */
@Repository
public final class AuditDataRepository extends JdbcRepositorySupport {
    public AuditDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
