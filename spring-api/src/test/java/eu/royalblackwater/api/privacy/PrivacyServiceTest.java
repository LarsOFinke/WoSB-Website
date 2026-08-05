package eu.royalblackwater.api.privacy;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.contract.DataSubjectRequestCreate;
import eu.royalblackwater.api.contract.PrivacyContactCreate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;

class PrivacyServiceTest {
    private static final Clock CLOCK = Clock.fixed(
            Instant.parse("2026-08-05T12:00:00Z"), ZoneOffset.UTC);

    @Test
    void normalizesPublicContactDataWithoutRecordingRequestMetadata() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.count(anyString(), anyMap())).thenReturn(0L);
        when(jdbc.insertReturningId(anyString(), anyMap())).thenReturn(17L);

        Map<String, Object> result = new PrivacyService(jdbc, CLOCK).createContact(
                new PrivacyContactCreate(
                        "  Please answer this privacy question.  ",
                        "  MEMBER@Example.COM ",
                        "  Privacy   question ",
                        ""),
                null);

        assertThat(result).containsEntry("id", 17L).containsEntry("status", "pending");
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, Object>> values = ArgumentCaptor.forClass(Map.class);
        verify(jdbc).insertReturningId(anyString(), values.capture());
        assertThat(values.getValue())
                .containsEntry("email", "member@example.com")
                .containsEntry("subject", "Privacy question")
                .containsEntry("message", "Please answer this privacy question.")
                .containsEntry("createdAt", LocalDateTime.of(2026, 8, 5, 12, 0))
                .doesNotContainKeys("ip", "ipAddress", "userAgent");
    }

    @Test
    void rateLimitsTheFourthRecentMessageForTheNormalizedAddress() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        when(jdbc.count(anyString(), anyMap())).thenReturn(3L);

        assertStatus(429, () -> new PrivacyService(jdbc, CLOCK).createContact(
                new PrivacyContactCreate("A sufficiently long message", "MEMBER@example.com", "Question", ""),
                null));
        verify(jdbc, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void protectsDeletionRequestsWithIdentityAndBootstrapChecks() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        PrivacyService service = new PrivacyService(jdbc, CLOCK);
        AuthenticatedUser member = new AuthenticatedUser(7, "member", "user", false, false, false);
        AuthenticatedUser bootstrap = new AuthenticatedUser(1, "admin", "admin", true, true, true);

        assertStatus(409, () -> service.createRequest(
                member, new DataSubjectRequestCreate("someone-else", null, "deletion")));
        assertStatus(409, () -> service.createRequest(
                bootstrap, new DataSubjectRequestCreate("admin", null, "deletion")));
        verify(jdbc, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void rejectsUnsupportedAndDuplicatePendingRequestTypes() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        PrivacyService service = new PrivacyService(jdbc, CLOCK);
        AuthenticatedUser member = new AuthenticatedUser(7, "member", "user", false, false, false);

        assertStatus(422, () -> service.createRequest(
                member, new DataSubjectRequestCreate(null, null, "export")));
        when(jdbc.count(anyString(), anyMap())).thenReturn(1L);
        assertStatus(409, () -> service.createRequest(
                member, new DataSubjectRequestCreate(null, null, "correction")));
        verify(jdbc, never()).insertReturningId(anyString(), anyMap());
    }

    private static void assertStatus(int status, ThrowingCall call) {
        assertThatThrownBy(call::run)
                .isInstanceOfSatisfying(ResponseStatusException.class,
                        exception -> assertThat(exception.getStatusCode().value()).isEqualTo(status));
    }

    @FunctionalInterface
    private interface ThrowingCall {
        void run();
    }
}
