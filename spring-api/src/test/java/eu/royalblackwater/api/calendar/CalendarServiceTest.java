package eu.royalblackwater.api.calendar;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.calendar.repository.CalendarRepository;
import eu.royalblackwater.api.calendar.service.CalendarService;
import eu.royalblackwater.api.dto.FleetEventCreate;
import eu.royalblackwater.api.raidhelper.service.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperPolicy;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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

class CalendarServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final AuthenticatedUser USER = new AuthenticatedUser(7, "captain", "member", false, false, false);

    @Test
    void listFailsClosedWhenQueryWouldExceedMaximumResultSize() {
        CalendarRepository repository = mock(CalendarRepository.class);
        RaidHelperLinkService links = mock(RaidHelperLinkService.class);
        when(links.officialFleetId()).thenReturn(1L);
        when(links.canManage(USER, null)).thenReturn(true);
        List<Map<String, Object>> rows = new ArrayList<>();
        for (int index = 0; index < 1001; index++) rows.add(Map.of());
        when(repository.query(anyString(), anyMap())).thenReturn(rows);

        assertThatThrownBy(() -> service(repository, links).list(USER, null, null, null, null, false))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(400));
        verify(links, never()).linksByEventIds(org.mockito.ArgumentMatchers.anyCollection());
    }

    @Test
    void createRejectsMissingTitleAndInvalidTimeWindowBeforePersistence() {
        CalendarRepository repository = mock(CalendarRepository.class);
        RaidHelperLinkService links = mock(RaidHelperLinkService.class);
        when(links.officialFleetId()).thenReturn(1L);
        LocalDateTime start = LocalDateTime.of(2030, 1, 15, 18, 0);

        FleetEventCreate noTitle = new FleetEventCreate(false, "other", null, start.plusHours(1), null,
                List.of(), false, null, start, "   ");
        FleetEventCreate invalidEnd = new FleetEventCreate(false, "other", null, start, null,
                List.of(), false, null, start, "Training");

        assertThatThrownBy(() -> service(repository, links).create(noTitle, USER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("Event title is required");
        assertThatThrownBy(() -> service(repository, links).create(invalidEnd, USER))
                .isInstanceOf(ResponseStatusException.class).hasMessageContaining("after event start");
        verify(repository, never()).insertReturningId(anyString(), anyMap());
    }

    private static CalendarService service(CalendarRepository repository, RaidHelperLinkService links) {
        return new CalendarService(repository, new RaidHelperPolicy(new tools.jackson.databind.ObjectMapper()), links,
                mock(AuditService.class), CLOCK);
    }
}
