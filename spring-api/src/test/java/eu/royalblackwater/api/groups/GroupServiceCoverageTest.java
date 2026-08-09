package eu.royalblackwater.api.groups;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.GroupJoinRequest;
import eu.royalblackwater.api.groups.repository.GroupRepository;
import eu.royalblackwater.api.groups.repository.queries.GroupQueries;
import eu.royalblackwater.api.groups.service.GroupService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GroupServiceCoverageTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void joinCoversBuildShipAndAdHocSelectionPathsAndCreatesResolvedSelectionRecord() {
        GroupRepository repository = mock(GroupRepository.class);
        ShipQueryService ships = mock(ShipQueryService.class);
        when(repository.count(anyString(), anyMap())).thenReturn(0L);
        when(repository.optional(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (GroupQueries.RESOLVE_SELECTION_SELECT_01.equals(sql)) {
                return Optional.of(Map.of("build_id", 30L, "ship_id", 40L, "ship_name", "Frigate", "ship_rate", 3L));
            }
            if (GroupQueries.RESOLVE_SELECTION_SELECT_02.equals(sql)) {
                return Optional.of(Map.of("id", 41L, "name", "Brig", "rate", 4L));
            }
            if (GroupQueries.JOIN_SELECT_02.equals(sql)) {
                return Optional.of(Map.of("display_name", "Captain Display"));
            }
            return Optional.of(groupRow("open", 0L, 5L, null, null));
        });
        when(repository.query(anyString(), anyMap())).thenReturn(List.of());
        GroupService service = new GroupService(repository, ships, mock(AuditService.class), CLOCK);

        var byBuild = service.join(1L, new GroupJoinRequest(30L, "captain", null, null, null, null, null), USER);
        var byShip = service.join(1L, new GroupJoinRequest(null, "Other", null, null, 41L, null, null), USER);
        var adHoc = service.join(1L, new GroupJoinRequest(null, "Other", null, null, null, " Cutter ", 5L), USER);

        assertThat(byBuild.id()).isEqualTo(1L);
        assertThat(byShip.id()).isEqualTo(1L);
        assertThat(adHoc.id()).isEqualTo(1L);
        verify(repository, org.mockito.Mockito.atLeast(3)).insertReturningId(anyString(), anyMap());
    }

    @Test
    void joinCoversClosedFullDuplicateAndRateBoundaries() {
        assertJoinBad(groupRow("closed", 0L, 5L, null, null), 0L,
                new GroupJoinRequest(null, "Captain", null, null, null, "Ship", null), "not open");
        assertJoinBad(groupRow("open", 5L, 5L, null, null), 0L,
                new GroupJoinRequest(null, "Captain", null, null, null, "Ship", null), "already full");
        assertJoinBad(groupRow("open", 0L, 5L, null, null), 1L,
                new GroupJoinRequest(null, "Captain", null, null, null, "Ship", null), "already joined");
        assertJoinBad(groupRow("open", 0L, 5L, 3L, 5L), 0L,
                new GroupJoinRequest(null, "Captain", null, null, null, "Ship", null), "requires a ship");
        assertJoinBad(groupRow("open", 0L, 5L, 3L, 5L), 0L,
                new GroupJoinRequest(null, "Captain", null, null, null, "Ship", 7L), "outside the allowed range");
    }

    @Test
    void closeCoversOwnerStaffAndAlreadyClosedBranches() {
        GroupRepository repository = mock(GroupRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(groupRow("open", 0L, 5L, null, null)));
        GroupService service = new GroupService(repository, mock(ShipQueryService.class), mock(AuditService.class), CLOCK);
        service.close(1L, USER);
        verify(repository).update(anyString(), anyMap());

        GroupRepository closedRepository = mock(GroupRepository.class);
        when(closedRepository.optional(anyString(), anyMap())).thenReturn(Optional.of(groupRow("closed", 0L, 5L, null, null)));
        new GroupService(closedRepository, mock(ShipQueryService.class), mock(AuditService.class), CLOCK).close(1L, USER);
        verify(closedRepository, org.mockito.Mockito.never()).update(anyString(), anyMap());
    }

    private static void assertJoinBad(Map<String, Object> row, long existingCount, GroupJoinRequest request, String message) {
        GroupRepository repository = mock(GroupRepository.class);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(row));
        when(repository.count(anyString(), anyMap())).thenReturn(existingCount);
        GroupService service = new GroupService(repository, mock(ShipQueryService.class), mock(AuditService.class), CLOCK);
        assertThatThrownBy(() -> service.join(1L, request, USER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining(message);
    }

    private static Map<String, Object> groupRow(String status, long active, long maximum, Long minRate, Long maxRate) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", 1L);
        row.put("active_count", active);
        row.put("max_members", maximum);
        row.put("status", status);
        row.put("expires_at", LocalDateTime.of(2030, 1, 16, 12, 0));
        row.put("min_ship_rate", minRate);
        row.put("max_ship_rate", maxRate);
        row.put("owner_id", 7L);
        row.put("owner_display_name", "Captain");
        row.put("title", "Operation");
        row.put("created_at", LocalDateTime.of(2030, 1, 15, 10, 0));
        row.put("updated_at", LocalDateTime.of(2030, 1, 15, 11, 0));
        row.put("allow_guests", true);
        return row;
    }
}
