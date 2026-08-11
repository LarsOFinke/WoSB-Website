package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.DataSubjectRequestResolve;
import eu.royalblackwater.api.dto.PersonalDataExportRead;
import eu.royalblackwater.api.dto.PrivacyContactResolve;
import eu.royalblackwater.api.privacy.mapper.PrivacyDtoMapper;
import eu.royalblackwater.api.privacy.repository.PrivacyDataRepository;
import eu.royalblackwater.api.privacy.service.PersonalDataExportService;
import eu.royalblackwater.api.privacy.service.PrivacyAdministrationService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
import java.sql.Timestamp;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class PrivacyServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-08-08T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void personalDataExportCoversEveryDeclaredRelationAndRedactsSecrets() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        PrivacyDtoMapper mapper = new PrivacyDtoMapper();
        PersonalDataExportService service = new PersonalDataExportService(repository, CLOCK, mapper);
        Map<String, Object> account = Map.of(
                "id", 7,
                "username", "captain",
                "password_hash", "must-not-leak",
                "token_hash", "must-not-leak",
                "consent_key", "must-not-leak",
                "avatar", new byte[] {1, 2},
                "updated_at", Timestamp.from(Instant.parse("2026-08-08T11:00:00Z")));

        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(account));
        when(repository.count(anyString(), anyMap())).thenReturn(1L);
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());

        PersonalDataExportRead result = service.build(USER);

        assertEquals(21, result.categories().size());
        assertEquals(LocalDateTime.of(2026, 8, 8, 12, 0), result.exportedAt());
        assertFalse(result.subject().containsKey("password_hash"));
        assertFalse(result.subject().containsKey("token_hash"));
        assertFalse(result.subject().containsKey("consent_key"));
        assertEquals("[binary omitted]", result.subject().get("avatar"));
        assertTrue(result.subject().get("updated_at") instanceof LocalDateTime);
    }

    @Test
    void personalDataExportFailsClosedWhenRelationMappingIsStale() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        PersonalDataExportService service = new PersonalDataExportService(repository, CLOCK, new PrivacyDtoMapper());
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 7)));
        when(repository.count(anyString(), anyMap())).thenReturn(0L);

        IllegalStateException error = assertThrows(IllegalStateException.class, () -> service.build(USER));

        assertTrue(error.getMessage().contains("mapping is stale"));
    }

    @Test
    void administrationRejectsInvalidDecisionBeforePersistence() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        PrivacyAdministrationService service = administration(repository);

        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.resolveContact(12, new PrivacyContactResolve("later", "Needs review"), USER));

        assertEquals(422, error.getStatusCode().value());
        verify(repository, never()).optional(anyString(), anyMap());
    }

    @Test
    void administrationRejectsAlreadyResolvedContact() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        PrivacyAdministrationService service = administration(repository);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("status", "completed")));

        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.resolveContact(12, new PrivacyContactResolve("reject", "Duplicate request"), USER));

        assertEquals(409, error.getStatusCode().value());
        verify(repository, never()).update(anyString(), anyMap());
    }

    @Test
    void administrationRejectsBootstrapAdministratorDeletion() {
        PrivacyDataRepository repository = mock(PrivacyDataRepository.class);
        PrivacyAdministrationService service = administration(repository);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of(
                "status", "pending",
                "request_type", "deletion",
                "subject_user_id", 1L,
                "subject_username", "bootstrap",
                "is_bootstrap_admin", true)));

        ResponseStatusException error = assertThrows(ResponseStatusException.class,
                () -> service.resolveRequest(33, new DataSubjectRequestResolve("complete", "Deletion approved"), USER));

        assertEquals(409, error.getStatusCode().value());
        verify(repository, never()).update(anyString(), anyMap());
    }

    private static PrivacyAdministrationService administration(PrivacyDataRepository repository) {
        return new PrivacyAdministrationService(repository, mock(PasswordHasher.class), mock(AuditService.class), CLOCK,
                mock(PrivacyDtoMapper.class));
    }
}
