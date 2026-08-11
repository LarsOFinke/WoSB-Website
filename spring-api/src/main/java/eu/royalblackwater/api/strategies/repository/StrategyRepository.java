package eu.royalblackwater.api.strategies.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

@Repository
public class StrategyRepository extends JdbcRepositorySupport {
    public StrategyRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
