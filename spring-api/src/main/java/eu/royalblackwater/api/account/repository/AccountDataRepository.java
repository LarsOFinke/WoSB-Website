package eu.royalblackwater.api.account.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the account domain. */
@Repository
public class AccountDataRepository extends JdbcRepositorySupport {
    public AccountDataRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
