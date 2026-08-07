package eu.royalblackwater.api.masterdata.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the masterdata domain. */
@Repository
public class MasterDataRepository extends JdbcRepositorySupport {
    public MasterDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
