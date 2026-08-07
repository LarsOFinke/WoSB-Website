package eu.royalblackwater.api.account;

import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.service.RegistrationAdministrationService;
import eu.royalblackwater.api.account.service.UserDirectoryService;
import eu.royalblackwater.api.audit.service.AuditService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RegistrationAdministrationServiceTest {
    @Test
    void mapsPendingRegistrationWithoutNullableUserReferenceLookup() {
        AccountDataRepository repository = mock(AccountDataRepository.class);
        UserDirectoryService users = mock(UserDirectoryService.class);
        AuditService audit = mock(AuditService.class);
        Clock clock = Clock.fixed(LocalDateTime.of(2030, 1, 1, 12, 0).toInstant(ZoneOffset.UTC), ZoneOffset.UTC);
        LocalDateTime createdAt = LocalDateTime.of(2030, 1, 1, 10, 0);

        when(repository.query(contains("from registration_requests"), anyMap())).thenReturn(List.of(Map.of(
                "id", 7L,
                "username", "pending-review",
                "display_name", "Pending Review",
                "wants_fleet_membership", false,
                "status", "pending",
                "created_at", createdAt,
                "updated_at", createdAt)));
        when(users.readMany(List.of())).thenReturn(Map.of());

        var result = new RegistrationAdministrationService(repository, users, audit, clock)
                .list("pending", null, null, null);

        assertThat(result).singleElement().satisfies(request -> {
            assertThat(request.id()).isEqualTo(7L);
            assertThat(request.createdUser()).isNull();
            assertThat(request.reviewedBy()).isNull();
            assertThat(request.status()).isEqualTo("pending");
        });
        verify(users).readMany(List.of());
    }
}
