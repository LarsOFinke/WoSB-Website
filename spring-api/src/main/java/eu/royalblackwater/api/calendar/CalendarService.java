package eu.royalblackwater.api.calendar;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.CalendarSquadRead;
import eu.royalblackwater.api.contract.FleetEventCreate;
import eu.royalblackwater.api.contract.FleetEventRead;
import eu.royalblackwater.api.contract.FleetEventUpdate;
import eu.royalblackwater.api.contract.RaidHelperEventLinkRead;
import eu.royalblackwater.api.contract.UserReferenceRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.RaidHelperLinkService;
import eu.royalblackwater.api.raidhelper.RaidHelperPolicy;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class CalendarService {
    private static final int MAX_RESULT_SIZE = 1000;
    private static final String EVENT_SELECT = """
            select e.*,s.name squad_name,s.slug squad_slug,s.fleet_id,
                   coalesce(nullif(up.display_name,''),u.username) owner_display_name
            from fleet_events e join users u on u.id=e.owner_id
            left join user_profiles up on up.user_id=u.id
            left join squads s on s.id=e.squad_id
            """;

    private final JdbcQueryService jdbc;
    private final RaidHelperPolicy categories;
    private final RaidHelperLinkService raidHelper;
    private final AuditService audit;
    private final Clock clock;

    public CalendarService(JdbcQueryService jdbc, RaidHelperPolicy categories,
                           RaidHelperLinkService raidHelper, AuditService audit, Clock clock) {
        this.jdbc = jdbc;
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
        StringBuilder sql = new StringBuilder(EVENT_SELECT + " where e.is_cancelled=false");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!managesFleet) {
            sql.append("""
                     and (e.squad_id is null or exists(
                       select 1 from squad_members sm join fleet_memberships fm on fm.id=sm.fleet_membership_id
                       where sm.squad_id=e.squad_id and fm.user_id=:userId and fm.status='active'))
                    """);
            parameters.put("userId", actor.id());
        }
        if (start != null) { sql.append(" and e.end_at>=:start"); parameters.put("start", start); }
        if (end != null) { sql.append(" and e.start_at<=:end"); parameters.put("end", end); }
        if (category != null && !category.isBlank()) {
            sql.append(" and e.category=:category"); parameters.put("category", categories.category(category));
        }
        if (fleetOnly) {
            sql.append(" and e.squad_id is null");
        } else if (squadId != null) {
            sql.append(" and e.squad_id=:squadId"); parameters.put("squadId", squadId);
        }
        sql.append(" order by e.start_at,e.id limit ").append(MAX_RESULT_SIZE + 1);
        List<Map<String, Object>> rows = jdbc.query(sql.toString(), parameters);
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
        return rows.stream().map(row -> read(row,
                managesFleet || nullableLong(row, "squad_id") != null
                        && managedSquads.contains(nullableLong(row, "squad_id")), links)).toList();
    }

    @Transactional(readOnly = true)
    public FleetEventRead get(long eventId, AuthenticatedUser actor) {
        Map<String, Object> row = visibleRow(eventId, actor);
        boolean canManage = raidHelper.canManage(actor, nullableLong(row, "squad_id"));
        Map<Long, List<RaidHelperEventLinkRead>> links = canManage
                ? raidHelper.linksByEventIds(List.of(eventId)) : Map.of();
        return read(row, canManage, links);
    }

    @Transactional
    public FleetEventRead create(FleetEventCreate payload, AuthenticatedUser actor) {
        ValidatedEvent value = validate(payload.title(), payload.category(), payload.description(), payload.location(),
                payload.startAt(), payload.endAt(), payload.allDay(), payload.squadId(),
                payload.raidHelperEnabled(), payload.raidHelperDispatches(), actor);
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into fleet_events
                  (title,category,description,location,start_at,end_at,all_day,owner_id,squad_id,
                   is_cancelled,raid_helper_enabled,created_at,updated_at)
                values (:title,:category,:description,:location,:startAt,:endAt,:allDay,:ownerId,:squadId,
                        false,:raidHelperEnabled,:now,:now) returning id
                """, value.parameters(actor.id(), now));
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
        jdbc.update("""
                update fleet_events set title=:title,category=:category,description=:description,location=:location,
                  start_at=:startAt,end_at=:endAt,all_day=:allDay,squad_id=:squadId,
                  raid_helper_enabled=:raidHelperEnabled,updated_at=:now where id=:id
                """, merge(value.parameters(actor.id(), now()), "id", eventId));
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
        jdbc.update("update fleet_events set is_cancelled=true,updated_at=:now where id=:id",
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
        return jdbc.optional(EVENT_SELECT + " where e.id=:id", Map.of("id", id)).orElseThrow(CalendarService::notFound);
    }

    private boolean canViewSquad(AuthenticatedUser actor, long squadId) {
        if (raidHelper.canManage(actor, squadId)) return true;
        return jdbc.count("""
                select count(*) from squad_members sm join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where sm.squad_id=:squadId and fm.user_id=:userId and fm.status='active'
                """, Map.of("squadId", squadId, "userId", actor.id())) > 0;
    }

    private Set<Long> managedSquadIds(int userId, long fleetId) {
        return jdbc.query("""
                select sm.squad_id from squad_members sm
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                join squad_roles sr on sr.id=sm.squad_role_id
                join squads s on s.id=sm.squad_id
                where fm.user_id=:userId and fm.status='active' and s.fleet_id=:fleetId
                  and s.is_active=true and sr.code in ('leader','officer')
                """, Map.of("userId", userId, "fleetId", fleetId)).stream()
                .map(row -> longValue(row, "squad_id")).collect(java.util.stream.Collectors.toUnmodifiableSet());
    }

    private ValidatedEvent validate(String title, String category, String description, String location,
                                    LocalDateTime startAt, LocalDateTime endAt, Boolean allDay, Long squadId,
                                    Boolean raidEnabled, List<eu.royalblackwater.api.contract.RaidHelperDispatchSelection> dispatches,
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
        List<eu.royalblackwater.api.contract.RaidHelperDispatchSelection> cleanDispatches =
                dispatches == null ? List.of() : List.copyOf(dispatches);
        if (cleanDispatches.size() > 20) throw bad("At most 20 Raid-Helper destinations may be selected.");
        return new ValidatedEvent(cleanTitle, cleanCategory, cleanDescription, cleanLocation,
                startAt, endAt, allDay != null && allDay, squadId, enabled, cleanDispatches);
    }

    private void validateScope(Long squadId, AuthenticatedUser actor) {
        raidHelper.requireScopeManager(actor, squadId);
        if (squadId == null) return;
        Map<String, Object> squad = jdbc.optional("select fleet_id,is_active from squads where id=:id", Map.of("id", squadId))
                .orElseThrow(() -> bad("Squad not found or archived."));
        if (!booleanValue(squad, "is_active") || longValue(squad, "fleet_id") != raidHelper.officialFleetId()) {
            throw bad("Squad not found, archived or outside the official fleet.");
        }
    }

    private FleetEventRead read(Map<String, Object> row, boolean canManage,
                                Map<Long, List<RaidHelperEventLinkRead>> links) {
        Long squadId = nullableLong(row, "squad_id");
        CalendarSquadRead squad = squadId == null ? null : new CalendarSquadRead(
                squadId, requiredString(row, "squad_name"), requiredString(row, "squad_slug"));
        long eventId = longValue(row, "id");
        return new FleetEventRead(booleanValue(row, "all_day"), canManage,
                requiredString(row, "category"), dateTime(row, "created_at"), string(row, "description"),
                dateTime(row, "end_at"), eventId, booleanValue(row, "is_cancelled"), string(row, "location"),
                new UserReferenceRead(requiredString(row, "owner_display_name"), longValue(row, "owner_id")),
                longValue(row, "owner_id"), booleanValue(row, "raid_helper_enabled"),
                canManage ? links.getOrDefault(eventId, List.of()) : List.of(),
                squadId == null ? "Fleet" : requiredString(row, "squad_name"), squadId == null ? "fleet" : "squad",
                squad, squadId, dateTime(row, "start_at"), requiredString(row, "title"), dateTime(row, "updated_at"));
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
                                  List<eu.royalblackwater.api.contract.RaidHelperDispatchSelection> dispatches) {
        Map<String, Object> parameters(int ownerId, LocalDateTime now) {
            return SqlParameters.ofNullable("title", title, "category", category, "description", description,
                    "location", location, "startAt", startAt, "endAt", endAt, "allDay", allDay,
                    "ownerId", ownerId, "squadId", squadId, "raidHelperEnabled", raidHelperEnabled, "now", now);
        }
    }
}
