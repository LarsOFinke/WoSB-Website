package eu.royalblackwater.api.calendar.controller;

import eu.royalblackwater.api.dto.FleetEventRead;
import java.util.List;
import eu.royalblackwater.api.calendar.service.CalendarService;
import eu.royalblackwater.api.dto.FleetEventCreate;
import eu.royalblackwater.api.dto.FleetEventUpdate;
import eu.royalblackwater.api.contract.api.CalendarApi;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.time.LocalDateTime;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class CalendarController extends ApiControllerSupport implements CalendarApi {

    private final CalendarService calendar;

    public CalendarController(CalendarService calendar) {
        this.calendar = calendar;
    }

    @Override
    public ResponseEntity<List<FleetEventRead>> getEvents(
            LocalDateTime start,
            LocalDateTime end,
            String category,
            Long squadId,
            boolean fleetOnly
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.list(actor,
                            start, end,
                            category, squadId,
                            fleetOnly), 200);
    }

    @Override
    public ResponseEntity<FleetEventRead> postEvent(
            FleetEventCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.create(body(body, FleetEventCreate.class), actor), 201);
    }

    @Override
    public ResponseEntity<Void> deleteEvent(
            long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        calendar.cancel(eventId, actor); return noContent();
    }

    @Override
    public ResponseEntity<FleetEventRead> getEventDetail(
            long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.get(eventId, actor), 200);
    }

    @Override
    public ResponseEntity<FleetEventRead> putEvent(
            long eventId,
            FleetEventUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.update(
                            eventId, body(body, FleetEventUpdate.class), actor), 200);
    }

    @Override
    public ResponseEntity<FleetEventRead> retryRaidHelperEvent(
            long eventId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(calendar.retry(eventId, actor), 200);
    }

    private static LocalDateTime dateTime(Object value) {
        return value instanceof LocalDateTime dateTime ? dateTime : null;
    }

    private static Long nullableLong(Object value) {
        return value instanceof Number number ? number.longValue() : null;
    }
}
