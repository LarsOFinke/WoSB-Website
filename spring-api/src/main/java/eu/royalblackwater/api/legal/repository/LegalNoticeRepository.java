package eu.royalblackwater.api.legal.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the legal domain. */
@Repository
public class LegalNoticeRepository extends JdbcRepositorySupport {
    public LegalNoticeRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
