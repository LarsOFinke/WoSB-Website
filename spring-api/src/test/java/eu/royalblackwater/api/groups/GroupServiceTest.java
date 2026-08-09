package eu.royalblackwater.api.groups;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.GroupCreate;
import eu.royalblackwater.api.groups.repository.GroupRepository;
import eu.royalblackwater.api.groups.service.GroupService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GroupServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void createRejectsInvalidFocusGroupSizeRateRangeAndSchedule() {
        GroupRepository repository = mock(GroupRepository.class);
        GroupService service = service(repository);
        LocalDateTime start = LocalDateTime.of(2030, 1, 15, 18, 0);

        assertBad(() -> service.create(group("invalid", 5L, null, null, null, null), USER), "Invalid group focus");
        assertBad(() -> service.create(group("pve_general", 1L, null, null, null, null), USER), "between 2 and 50");
        assertBad(() -> service.create(group("pve_general", 5L, 8L, 4L, null, null), USER), "rate");
        assertBad(() -> service.create(group("pve_general", 5L, null, null, start, start), USER), "after start time");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void closeHidesOwnershipBoundaryFromNonOwner() {
        GroupRepository repository = mock(GroupRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of(
                "id", 3L, "owner_id", 99L, "status", "open")));

        assertThatThrownBy(() -> service(repository).close(3, USER))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(403));
    }

    private static GroupCreate group(String focus, Long maxMembers, Long minRate, Long maxRate,
                                     LocalDateTime start, LocalDateTime end) {
        return new GroupCreate(null, true, null, null, null, null, focus, maxMembers, maxRate, minRate,
                end, start, "Operation");
    }

    private static void assertBad(org.assertj.core.api.ThrowableAssert.ThrowingCallable call, String message) {
        assertThatThrownBy(call).isInstanceOf(ResponseStatusException.class).hasMessageContaining(message);
    }

    private static GroupService service(GroupRepository repository) {
        return new GroupService(repository, mock(ShipQueryService.class), mock(AuditService.class), CLOCK);
    }
}
