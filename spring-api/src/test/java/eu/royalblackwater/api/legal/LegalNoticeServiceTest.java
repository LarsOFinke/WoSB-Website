package eu.royalblackwater.api.legal;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.config.LegalNoticeProperties;
import eu.royalblackwater.api.legal.repository.LegalNoticeRepository;
import eu.royalblackwater.api.legal.service.LegalNoticeService;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class LegalNoticeServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void publicNoticeFailsClosedWhenNoPublishedSingletonExists() {
        LegalNoticeRepository repository = mock(LegalNoticeRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.empty());

        var notice = service(repository).publicNotice();

        assertThat(notice.published()).isFalse();
        assertThat(notice.providerName()).isNull();
    }

    @Test
    void adminReadEnsuresEnvironmentBackedSingletonBeforeReading() {
        LegalNoticeRepository repository = mock(LegalNoticeRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(java.util.Map.of(
                "published", false,
                "is_customized", false,
                "updated_at", java.time.LocalDateTime.of(2030, 1, 15, 12, 0),
                "updated_by_username", "environment")));

        service(repository).adminNotice();

        verify(repository).update(anyString(), anyMap());
        verify(repository).optional(anyString(), anyMap());
    }

    private static LegalNoticeService service(LegalNoticeRepository repository) {
        return new LegalNoticeService(repository, mock(LegalNoticeProperties.class), mock(AuditService.class), CLOCK);
    }
}
