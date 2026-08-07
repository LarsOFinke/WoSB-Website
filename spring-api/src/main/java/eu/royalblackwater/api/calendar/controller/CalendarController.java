package eu.royalblackwater.api.calendar.controller;

import eu.royalblackwater.api.calendar.service.CalendarService;
import eu.royalblackwater.api.dto.FleetEventCreate;
import eu.royalblackwater.api.dto.FleetEventRead;
import eu.royalblackwater.api.dto.FleetEventUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class CalendarController extends ApiControllerSupport {

    private final CalendarService calendar;

    public CalendarController(CalendarService calendar) {
        this.calendar = calendar;
    }

    @GetMapping("/api/calendar/events")
    public ResponseEntity<List<FleetEventRead>> getEvents(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) @RequestParam(name = "start", required = false) LocalDateTime start,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) @RequestParam(name = "end", required = false) LocalDateTime end,
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "squad_id", required = false) Long squadId,
            @RequestParam(name = "fleet_only", defaultValue = "false") boolean fleetOnly
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.list(actor,
                            start, end,
                            category, squadId,
                            fleetOnly), 200);
    }

    @PostMapping("/api/calendar/events")
    public ResponseEntity<FleetEventRead> postEvent(
            @Valid @RequestBody FleetEventCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.create(body, actor), 201);
    }

    @DeleteMapping("/api/calendar/events/{event_id}")
    public ResponseEntity<Void> deleteEvent(
            @PathVariable("event_id") long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        calendar.cancel(eventId, actor); return noContent();
    }

    @GetMapping("/api/calendar/events/{event_id}")
    public ResponseEntity<FleetEventRead> getEventDetail(
            @PathVariable("event_id") long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.get(eventId, actor), 200);
    }

    @PutMapping("/api/calendar/events/{event_id}")
    public ResponseEntity<FleetEventRead> putEvent(
            @PathVariable("event_id") long eventId,
            @Valid @RequestBody FleetEventUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.update(
                            eventId, body, actor), 200);
    }

    @PostMapping("/api/calendar/events/{event_id}/raid-helper/retry")
    public ResponseEntity<FleetEventRead> retryRaidHelperEvent(
            @PathVariable("event_id") long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.retry(eventId, actor), 200);
    }
}
