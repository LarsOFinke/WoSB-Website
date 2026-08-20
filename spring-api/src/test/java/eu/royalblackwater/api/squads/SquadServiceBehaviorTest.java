package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.SquadCreate;
import eu.royalblackwater.api.fleet.service.FleetAccessPolicy;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.squads.repository.SquadRepository;
import eu.royalblackwater.api.squads.service.SquadAccessPolicy;
import eu.royalblackwater.api.squads.service.SquadService;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class SquadServiceBehaviorTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-08-08T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser ACTOR = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void createFailsClosedWhenOfficialFleetIsMissing() {
        SquadRepository repository = mock(SquadRepository.class);
        SquadService service = new SquadService(repository, mock(FleetAccessPolicy.class), mock(SquadAccessPolicy.class),
                mock(AuditService.class), CLOCK);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.empty());
        SquadCreate payload = new SquadCreate(null, null, 42, 10L, "Vanguard");

        ResponseStatusException error = assertThrows(ResponseStatusException.class, () -> service.create(payload, ACTOR));

        assertEquals(400, error.getStatusCode().value());
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    @Test
    void rosterRequiresStaffBeforeReturningPrivateFleetRoster() {
        SquadRepository repository = mock(SquadRepository.class);
        SquadService service = new SquadService(repository, mock(FleetAccessPolicy.class),
                mock(SquadAccessPolicy.class), mock(AuditService.class), CLOCK);
        when(repository.optional(anyString(), anyMap())).thenReturn(Optional.of(Map.of("id", 9L)));

        ResponseStatusException error = assertThrows(ResponseStatusException.class, () -> service.roster(ACTOR));

        assertEquals(403, error.getStatusCode().value());
        verify(repository, never()).query(anyString(), anyMap());
    }
}
