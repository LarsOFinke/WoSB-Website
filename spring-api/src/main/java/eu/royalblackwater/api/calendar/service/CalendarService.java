package eu.royalblackwater.api.calendar.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.calendar.mapper.CalendarDtoMapper;
import eu.royalblackwater.api.calendar.repository.CalendarRepository;
import eu.royalblackwater.api.calendar.repository.queries.CalendarQueries;
import eu.royalblackwater.api.dto.CalendarSquadRead;
import eu.royalblackwater.api.dto.FleetEventCreate;
import eu.royalblackwater.api.dto.FleetEventRead;
import eu.royalblackwater.api.dto.FleetEventUpdate;
import eu.royalblackwater.api.dto.RaidHelperDispatchSelection;
import eu.royalblackwater.api.dto.RaidHelperEventLinkRead;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.service.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.service.RaidHelperPolicy;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class CalendarService {
    private static final int MAX_RESULT_SIZE = 1000;

    private final CalendarRepository repository;
    private final RaidHelperPolicy categories;
    private final RaidHelperLinkService raidHelper;
    private final AuditService audit;
    private final Clock clock;

    public CalendarService(CalendarRepository repository, RaidHelperPolicy categories,
                           RaidHelperLinkService raidHelper, AuditService audit, Clock clock) {
        this.repository = repository;
        this.categories = categories;
        this.raidHelper = raidHelper;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<FleetEventRead> list(AuthenticatedUser actor, LocalDateTime start, LocalDateTime end,
                                     String category, Long squadId, boolean fleetOnly) {
        long fleetId = raidHelper.officialFleetId();
        boolean managesFleet = raidHelper.canManage(actor, null);
        StringBuilder sql = new StringBuilder(CalendarQueries.EVENT_SELECT + CalendarQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!managesFleet) {
            sql.append(CalendarQueries.LIST_AND_01);
            parameters.put("userId", actor.id());
        }
        if (start != null) { sql.append(CalendarQueries.LIST_AND_02); parameters.put("start", start); }
        if (end != null) { sql.append(CalendarQueries.LIST_AND_03); parameters.put("end", end); }
        if (category != null && !category.isBlank()) {
            sql.append(CalendarQueries.LIST_AND_04); parameters.put("category", categories.category(category));
        }
        if (fleetOnly) {
            sql.append(CalendarQueries.LIST_AND_05);
        } else if (squadId != null) {
            sql.append(CalendarQueries.LIST_AND_06); parameters.put("squadId", squadId);
        }
        sql.append(CalendarQueries.LIST_ORDER_BY_01).append(MAX_RESULT_SIZE + 1);
        List<Map<String, Object>> rows = repository.query(sql.toString(), parameters);
        if (rows.size() > MAX_RESULT_SIZE) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "The calendar query is too broad. Select a smaller date range.");
        }
        Set<Long> managedSquads = managesFleet ? Set.of() : managedSquadIds(actor.id(), fleetId);
        List<Long> managedEvents = rows.stream()
                .filter(row -> managesFleet || nullableLong(row, "squad_id") != null
                        && managedSquads.contains(nullableLong(row, "squad_id")))
                .map(row -> longValue(row, "id")).toList();
        Map<Long, List<RaidHelperEventLinkRead>> links = raidHelper.linksByEventIds(managedEvents);
        return rows.stream().map(row -> CalendarDtoMapper.event(row,
                managesFleet || nullableLong(row, "squad_id") != null
                        && managedSquads.contains(nullableLong(row, "squad_id")), links)).toList();
    }

    @Transactional(readOnly = true)
    public FleetEventRead get(long eventId, AuthenticatedUser actor) {
        Map<String, Object> row = visibleRow(eventId, actor);
        boolean canManage = raidHelper.canManage(actor, nullableLong(row, "squad_id"));
        Map<Long, List<RaidHelperEventLinkRead>> links = canManage
                ? raidHelper.linksByEventIds(List.of(eventId)) : Map.of();
        return CalendarDtoMapper.event(row, canManage, links);
    }

    @Transactional
    public FleetEventRead create(FleetEventCreate payload, AuthenticatedUser actor) {
        ValidatedEvent value = validate(payload.title(), payload.category(), payload.description(), payload.location(),
                payload.startAt(), payload.endAt(), payload.allDay(), payload.squadId(),
                payload.raidHelperEnabled(), payload.raidHelperDispatches(), actor);
        LocalDateTime now = now();
        long id = repository.insertReturningId(CalendarQueries.CREATE_INSERT_01, value.parameters(actor.id(), now));
        raidHelper.configure(id, value.category(), value.squadId(),
                value.raidHelperEnabled() ? value.dispatches() : List.of(), actor);
        audit.record(actor, "calendar_event", id, "create", "Calendar event created.",
                List.of("title", "category", "start_at", "end_at", "squad_id", "raid_helper"));
        return get(id, actor);
    }

    @Transactional
    public FleetEventRead update(long eventId, FleetEventUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> current = row(eventId);
        if (booleanValue(current, "is_cancelled")) throw notFound();
        raidHelper.requireScopeManager(actor, nullableLong(current, "squad_id"));
        ValidatedEvent value = validate(payload.title(), payload.category(), payload.description(), payload.location(),
                payload.startAt(), payload.endAt(), payload.allDay(), payload.squadId(),
                payload.raidHelperEnabled(), payload.raidHelperDispatches(), actor);
        repository.update(CalendarQueries.UPDATE_UPDATE_01, merge(value.parameters(actor.id(), now()), "id", eventId));
        raidHelper.configure(eventId, value.category(), value.squadId(),
                value.raidHelperEnabled() ? value.dispatches() : List.of(), actor);
        audit.record(actor, "calendar_event", eventId, "update", "Calendar event updated.",
                List.of("title", "category", "start_at", "end_at", "squad_id", "raid_helper"));
        return get(eventId, actor);
    }

    @Transactional
    public FleetEventRead retry(long eventId, AuthenticatedUser actor) {
        Map<String, Object> current = row(eventId);
        if (booleanValue(current, "is_cancelled")) throw notFound();
        raidHelper.requireScopeManager(actor, nullableLong(current, "squad_id"));
        raidHelper.queueRetry(eventId);
        return get(eventId, actor);
    }

    @Transactional
    public void cancel(long eventId, AuthenticatedUser actor) {
        Map<String, Object> current = row(eventId);
        if (booleanValue(current, "is_cancelled")) throw notFound();
        raidHelper.requireScopeManager(actor, nullableLong(current, "squad_id"));
        repository.update(CalendarQueries.CANCEL_UPDATE_01,
                Map.of("now", now(), "id", eventId));
        raidHelper.queueCancellation(eventId);
        audit.record(actor, "calendar_event", eventId, "cancel", "Calendar event cancelled.",
                List.of("is_cancelled"));
    }

    private Map<String, Object> visibleRow(long id, AuthenticatedUser actor) {
        Map<String, Object> row = row(id);
        if (booleanValue(row, "is_cancelled")) throw notFound();
        Long squadId = nullableLong(row, "squad_id");
        if (squadId != null && !canViewSquad(actor, squadId)) throw notFound();
        return row;
    }

    private Map<String, Object> row(long id) {
        return repository.optional(CalendarQueries.EVENT_SELECT + CalendarQueries.ROW_WHERE_01, Map.of("id", id)).orElseThrow(CalendarService::notFound);
    }

    private boolean canViewSquad(AuthenticatedUser actor, long squadId) {
        if (raidHelper.canManage(actor, squadId)) return true;
        return repository.count(CalendarQueries.CAN_VIEW_SQUAD_SELECT_01, Map.of("squadId", squadId, "userId", actor.id())) > 0;
    }

    private Set<Long> managedSquadIds(int userId, long fleetId) {
        return repository.query(CalendarQueries.MANAGED_SQUAD_IDS_SELECT_01, Map.of("userId", userId, "fleetId", fleetId)).stream()
                .map(row -> longValue(row, "squad_id")).collect(java.util.stream.Collectors.toUnmodifiableSet());
    }

    private ValidatedEvent validate(String title, String category, String description, String location,
                                    LocalDateTime startAt, LocalDateTime endAt, Boolean allDay, Long squadId,
                                    Boolean raidEnabled, List<eu.royalblackwater.api.dto.RaidHelperDispatchSelection> dispatches,
                                    AuthenticatedUser actor) {
        String cleanTitle = title == null ? "" : title.strip();
        if (cleanTitle.isEmpty()) throw bad("Event title is required.");
        if (startAt == null || endAt == null || !endAt.isAfter(startAt)) {
            throw bad("Event end must be after event start.");
        }
        String cleanDescription = clean(description, 3000, "Event description");
        String cleanLocation = clean(location, 200, "Event location");
        String cleanCategory = categories.category(category == null || category.isBlank() ? "other" : category);
        validateScope(squadId, actor);
        boolean enabled = raidEnabled == null || raidEnabled;
        List<eu.royalblackwater.api.dto.RaidHelperDispatchSelection> cleanDispatches =
                dispatches == null ? List.of() : List.copyOf(dispatches);
        if (cleanDispatches.size() > 20) throw bad("At most 20 Raid-Helper destinations may be selected.");
        return new ValidatedEvent(cleanTitle, cleanCategory, cleanDescription, cleanLocation,
                startAt, endAt, allDay != null && allDay, squadId, enabled, cleanDispatches);
    }

    private void validateScope(Long squadId, AuthenticatedUser actor) {
        raidHelper.requireScopeManager(actor, squadId);
        if (squadId == null) return;
        Map<String, Object> squad = repository.optional(CalendarQueries.VALIDATE_SCOPE_SELECT_01, Map.of("id", squadId))
                .orElseThrow(() -> bad("Squad not found or archived."));
        if (!booleanValue(squad, "is_active") || longValue(squad, "fleet_id") != raidHelper.officialFleetId()) {
            throw bad("Squad not found, archived or outside the official fleet.");
        }
    }


    private static String clean(String value, int max, String label) {
        if (value == null || value.isBlank()) return null;
        String clean = value.strip();
        if (clean.length() > max) throw bad(label + " is too long.");
        return clean;
    }

    private static Map<String, Object> merge(Map<String, Object> source, String name, Object value) {
        LinkedHashMap<String, Object> result = new LinkedHashMap<>(source); result.put(name, value); return result;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Event not found."); }

    private record ValidatedEvent(String title, String category, String description, String location,
                                  LocalDateTime startAt, LocalDateTime endAt, boolean allDay, Long squadId,
                                  boolean raidHelperEnabled,
                                  List<eu.royalblackwater.api.dto.RaidHelperDispatchSelection> dispatches) {
        Map<String, Object> parameters(int ownerId, LocalDateTime now) {
            return SqlParameters.ofNullable("title", title, "category", category, "description", description,
                    "location", location, "startAt", startAt, "endAt", endAt, "allDay", allDay,
                    "ownerId", ownerId, "squadId", squadId, "raidHelperEnabled", raidHelperEnabled, "now", now);
        }
    }
}
