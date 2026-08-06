package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.config.PrivacyRetentionProperties;
import eu.royalblackwater.api.privacy.repository.PrivacyDataRepository;
import eu.royalblackwater.api.privacy.service.PrivacyRetentionService;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class PrivacyRetentionServiceTest {
    @Test
    void deletesOnlyExpiredConsentAndResolvedPrivacyRecordsWithConfiguredCutoffs() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        when(repository.update(anyString(), anyMap())).thenReturn(4, 2, 3);
        Clock clock = Clock.fixed(Instant.parse("2026-08-05T12:00:00Z"), ZoneOffset.UTC);
        PrivacyRetentionService service = new PrivacyRetentionService(
                repository,
                new PrivacyRetentionProperties(
                        Duration.ofDays(400), Duration.ofDays(90), Duration.ofHours(24)),
                clock);

        PrivacyRetentionService.CleanupResult result = service.cleanExpiredData();

        assertThat(result).isEqualTo(new PrivacyRetentionService.CleanupResult(4, 2, 3));
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, ?>> parameters = ArgumentCaptor.forClass(Map.class);
        ArgumentCaptor<String> sql = ArgumentCaptor.forClass(String.class);
        verify(repository, times(3)).update(sql.capture(), parameters.capture());
        assertThat(sql.getAllValues().get(0)).contains("cookie_consent_decisions").doesNotContain("status");
        assertThat(parameters.getAllValues().get(0).get("cutoff"))
                .isEqualTo(LocalDateTime.of(2025, 7, 1, 12, 0));
        assertThat(sql.getAllValues().get(1))
                .contains("data_subject_requests", "status in ('completed', 'rejected')", "resolved_at < :cutoff");
        assertThat(parameters.getAllValues().get(1).get("cutoff"))
                .isEqualTo(LocalDateTime.of(2026, 5, 7, 12, 0));
        assertThat(sql.getAllValues().get(2))
                .contains("privacy_contact_requests", "status in ('completed', 'rejected')", "resolved_at < :cutoff");
    }
}
