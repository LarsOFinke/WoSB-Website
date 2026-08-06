package eu.royalblackwater.api.webhooks.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import org.springframework.stereotype.Repository;

/** Module-owned persistence boundary for the webhooks domain. */
@Repository
public final class WebhookRepository extends JdbcRepositorySupport {
    public WebhookRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }
}
