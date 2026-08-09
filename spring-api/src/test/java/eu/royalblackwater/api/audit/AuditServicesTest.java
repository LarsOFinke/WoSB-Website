package eu.royalblackwater.api.audit;

import eu.royalblackwater.api.audit.repository.AuditDataRepository;
import eu.royalblackwater.api.audit.service.AuditLogQueryService;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AuditServicesTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void queryRejectsInvalidBoundsAndBuildsNormalizedFilters() {
        AuditDataRepository repository = mock(AuditDataRepository.class);
        AuditLogQueryService service = new AuditLogQueryService(repository, new ObjectMapper());

        assertThatThrownBy(() -> service.list(null, null, null, null, null, 0))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(400));
        assertThatThrownBy(() -> service.list(null, null, null,
                LocalDate.of(2030, 2, 1), LocalDate.of(2030, 1, 1), 50))
                .isInstanceOf(ResponseStatusException.class);

        when(repository.query(anyString(), anyMap())).thenReturn(List.of());
        service.list(" user ", " update ", " cap ", LocalDate.of(2030, 1, 1), LocalDate.of(2030, 1, 2), 25);

        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).query(anyString(), parameters.capture());
        assertThat(parameters.getValue()).containsEntry("entityType", "user")
                .containsEntry("action", "update")
                .containsEntry("actor", "%cap%")
                .containsEntry("limit", 25L)
                .containsKeys("fromDate", "toDate");
    }

    @Test
    void recordNormalizesChangedFieldsAndCapsSummaryLength() {
        AuditDataRepository repository = mock(AuditDataRepository.class);
        AuditService service = new AuditService(repository, new ObjectMapper(), CLOCK);
        String summary = "x".repeat(700);

        service.record(ACTOR, "user", 9, "update", summary,
                List.of(" role ", "", "role", "active", "  active  "));

        ArgumentCaptor<Map<String, Object>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(repository).update(anyString(), parameters.capture());
        assertThat(parameters.getValue()).containsEntry("actorId", 7)
                .containsEntry("username", "captain")
                .containsEntry("entityId", "9");
        assertThat(String.valueOf(parameters.getValue().get("summary"))).hasSize(500);
        assertThat(String.valueOf(parameters.getValue().get("changedFields")))
                .contains("active", "role")
                .doesNotContain("role ");
    }
}
