package eu.royalblackwater.api.calendar;

import eu.royalblackwater.api.contract.FleetEventCreate;
import eu.royalblackwater.api.contract.FleetEventUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class CalendarOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_events_api_calendar_events_get",
            "post_event_api_calendar_events_post",
            "get_event_detail_api_calendar_events__event_id__get",
            "put_event_api_calendar_events__event_id__put",
            "retry_raid_helper_event_api_calendar_events__event_id__raid_helper_retry_post",
            "delete_event_api_calendar_events__event_id__delete");

    private final CalendarService calendar;

    public CalendarOperationHandler(CalendarService calendar) {
        this.calendar = calendar;
    }

    @Override
    public Set<String> operations() {
        return OPERATIONS;
    }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "get_events_api_calendar_events_get" -> calendar.list(actor,
                    dateTime(parameters.get("start")), dateTime(parameters.get("end")),
                    stringParameter(parameters, "category"), nullableLong(parameters.get("squad_id")),
                    booleanParameter(parameters, "fleet_only", false));
            case "post_event_api_calendar_events_post" -> calendar.create(body(body, FleetEventCreate.class), actor);
            case "get_event_detail_api_calendar_events__event_id__get" ->
                    calendar.get(longParameter(parameters, "event_id"), actor);
            case "put_event_api_calendar_events__event_id__put" -> calendar.update(
                    longParameter(parameters, "event_id"), body(body, FleetEventUpdate.class), actor);
            case "retry_raid_helper_event_api_calendar_events__event_id__raid_helper_retry_post" ->
                    calendar.retry(longParameter(parameters, "event_id"), actor);
            case "delete_event_api_calendar_events__event_id__delete" -> {
                calendar.cancel(longParameter(parameters, "event_id"), actor); yield null;
            }
            default -> throw new IllegalStateException("Unsupported calendar operation: " + operationId);
        };
    }

    private static LocalDateTime dateTime(Object value) {
        return value instanceof LocalDateTime dateTime ? dateTime : null;
    }

    private static Long nullableLong(Object value) {
        return value instanceof Number number ? number.longValue() : null;
    }
}
