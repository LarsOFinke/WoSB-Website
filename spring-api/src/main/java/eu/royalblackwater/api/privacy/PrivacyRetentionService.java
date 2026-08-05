package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.config.PrivacyRetentionProperties;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@ConditionalOnProperty(name = "rbf.scheduling.enabled", havingValue = "true", matchIfMissing = true)
public class PrivacyRetentionService {
    private static final Logger LOG = LoggerFactory.getLogger(PrivacyRetentionService.class);
    private final JdbcQueryService jdbc;
    private final PrivacyRetentionProperties properties;
    private final Clock clock;

    public PrivacyRetentionService(
            JdbcQueryService jdbc,
            PrivacyRetentionProperties properties,
            Clock clock) {
        this.jdbc = jdbc;
        this.properties = properties;
        this.clock = clock;
    }

    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void cleanAfterStartup() {
        clean();
    }

    @Scheduled(fixedDelayString = "${rbf.privacy.retention-interval:PT24H}")
    @Transactional
    public CleanupResult cleanExpiredData() {
        return clean();
    }

    private CleanupResult clean() {
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        int consentDecisions = jdbc.update("""
                delete from cookie_consent_decisions
                where created_at < :cutoff
                """, Map.of("cutoff", now.minus(properties.cookieConsentRetention())));
        Map<String, Object> resolvedCutoff = Map.of(
                "cutoff", now.minus(properties.resolvedRequestRetention()));
        int subjectRequests = jdbc.update("""
                delete from data_subject_requests
                where status in ('completed', 'rejected') and resolved_at < :cutoff
                """, resolvedCutoff);
        int contacts = jdbc.update("""
                delete from privacy_contact_requests
                where status in ('completed', 'rejected') and resolved_at < :cutoff
                """, resolvedCutoff);
        CleanupResult result = new CleanupResult(consentDecisions, subjectRequests, contacts);
        if (result.total() > 0) {
            LOG.info("privacy_retention_cleanup consentDecisions={} subjectRequests={} contacts={}",
                    result.consentDecisions(), result.subjectRequests(), result.contacts());
        }
        return result;
    }

    public record CleanupResult(int consentDecisions, int subjectRequests, int contacts) {
        int total() {
            return consentDecisions + subjectRequests + contacts;
        }
    }
}
