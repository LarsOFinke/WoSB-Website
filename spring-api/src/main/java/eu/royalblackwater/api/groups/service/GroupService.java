package eu.royalblackwater.api.groups.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.GroupCreate;
import eu.royalblackwater.api.dto.GroupJoinRequest;
import eu.royalblackwater.api.dto.GroupMemberRead;
import eu.royalblackwater.api.dto.GroupRead;
import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.groups.mapper.GroupDtoMapper;
import eu.royalblackwater.api.groups.repository.GroupRepository;
import eu.royalblackwater.api.groups.repository.queries.GroupQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class GroupService {
    private static final Set<String> FOCUS = Set.of(
            "pve_farming", "pve_imp_hunting", "pve_general", "pvp_open_world",
            "pvp_arena", "pvp_general", "trading", "other");
    private final GroupRepository repository;
    private final ShipQueryService ships;
    private final AuditService audit;
    private final Clock clock;

    public GroupService(GroupRepository repository, ShipQueryService ships, AuditService audit, Clock clock) {
        this.repository = repository;
        this.ships = ships;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<GroupRead> list(String search, String focus, Long minRate, Long maxRate, Integer ownerId) {
        validateRates(minRate, maxRate);
        StringBuilder sql = new StringBuilder(GroupQueries.GROUP_SELECT + GroupQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (ownerId == null) sql.append(GroupQueries.LIST_AND_01);
        else { sql.append(GroupQueries.LIST_AND_02); parameters.put("ownerId", ownerId); }
        if (search != null && !search.isBlank()) {
            sql.append(GroupQueries.LIST_AND_03);
            parameters.put("search", "%" + search.strip().toLowerCase(Locale.ROOT) + "%");
        }
        if (focus != null && !focus.isBlank()) {
            sql.append(GroupQueries.LIST_AND_04); parameters.put("focus", focus.strip().toLowerCase(Locale.ROOT));
        }
        if (minRate != null) {
            sql.append(GroupQueries.LIST_AND_05); parameters.put("minRate", minRate);
        }
        if (maxRate != null) {
            sql.append(GroupQueries.LIST_AND_06); parameters.put("maxRate", maxRate);
        }
        sql.append(ownerId == null
                ? GroupQueries.LIST_ORDER_BY_01
                : GroupQueries.LIST_ORDER_BY_02);
        return repository.query(sql.toString(), parameters).stream().map(this::read).toList();
    }

    @Transactional(readOnly = true)
    public GroupRead get(long id) {
        return read(raw(id));
    }

    @Transactional
    public GroupRead create(GroupCreate payload, AuthenticatedUser actor) {
        String focus = payload.focus() == null ? "pve_general" : payload.focus().strip().toLowerCase(Locale.ROOT);
        if (!FOCUS.contains(focus)) throw bad("Invalid group focus.");
        long maxMembers = payload.maxMembers() == null ? 5 : payload.maxMembers();
        if (maxMembers < 2 || maxMembers > 50) throw bad("Group size must be between 2 and 50.");
        validateRates(payload.minShipRate(), payload.maxShipRate());
        if (payload.scheduledStartAt() != null && payload.scheduledEndAt() != null
                && !payload.scheduledEndAt().isAfter(payload.scheduledStartAt())) {
            throw bad("End time must be after start time.");
        }
        LocalDateTime now = UtcDateTimes.now(clock);
        long id = repository.insertReturningId(GroupQueries.CREATE_INSERT_01, SqlParameters.ofNullable(
                        "title", required(payload.title()), "focus", focus,
                        "description", blank(payload.description()), "expectations", blank(payload.expectations()),
                        "activityPlan", blank(payload.activityPlan()), "contactNote", blank(payload.contactNote()),
                        "startAt", payload.scheduledStartAt(), "endAt", payload.scheduledEndAt(),
                        "maxMembers", maxMembers, "minRate", payload.minShipRate(), "maxRate", payload.maxShipRate(),
                        "allowGuests", payload.allowGuests() == null || payload.allowGuests(),
                        "fleetRestriction", blank(payload.fleetRestriction()), "ownerId", actor.id(),
                        "now", now, "expiresAt", now.plusHours(24)));
        audit.record(actor, "group", id, "create", "Group “" + required(payload.title()) + "” created.",
                List.of("title", "focus", "max_members", "ship_rate", "schedule"));
        return get(id);
    }

    @Transactional
    public GroupRead join(long groupId, GroupJoinRequest payload, AuthenticatedUser actor) {
        Map<String, Object> group = raw(groupId);
        long active = RowValues.longValue(group, "active_count");
        long maximum = RowValues.longValue(group, "max_members");
        if (!"open".equals(group.get("status")) || !RowValues.dateTime(group, "expires_at").isAfter(UtcDateTimes.now(clock))) {
            throw bad("This group is not open for new members.");
        }
        if (active >= maximum) throw bad("This group is already full.");
        if (repository.count(GroupQueries.JOIN_SELECT_01, Map.of("groupId", groupId, "userId", actor.id())) > 0) {
            throw bad("You already joined this group.");
        }
        ResolvedSelection selection = resolveSelection(payload, actor);
        requireAllowedRate(group, selection.shipRate());
        String displayName = required(payload.displayName());
        if (displayName.equals(actor.username())) {
            displayName = repository.optional(GroupQueries.JOIN_SELECT_02, Map.of("id", actor.id())).map(row -> String.valueOf(row.get("display_name"))).orElse(displayName);
        }
        LocalDateTime now = UtcDateTimes.now(clock);
        repository.insertReturningId(GroupQueries.JOIN_INSERT_01, SqlParameters.ofNullable(
                        "groupId", groupId, "userId", actor.id(), "displayName", displayName,
                        "fleetName", blank(payload.fleetName()), "shipId", selection.shipId(),
                        "buildId", selection.buildId(), "shipName", selection.shipName(),
                        "shipRate", selection.shipRate(), "note", blank(payload.note()), "now", now));
        if (active + 1 >= maximum) {
            repository.update(GroupQueries.JOIN_UPDATE_01,
                    Map.of("now", now, "id", groupId));
        }
        audit.record(actor, "group", groupId, GroupQueries.JOIN_JOIN_01, "Joined group #" + groupId + ".", List.of("members"));
        return get(groupId);
    }

    @Transactional
    public void close(long groupId, AuthenticatedUser actor) {
        Map<String, Object> group = raw(groupId);
        if (RowValues.longValue(group, "owner_id") != actor.id() && !actor.staff()) {
            throw new ResponseStatusException(FORBIDDEN, "You can only close your own groups.");
        }
        if (!"closed".equals(group.get("status"))) {
            LocalDateTime now = UtcDateTimes.now(clock);
            repository.update(GroupQueries.CLOSE_UPDATE_01,
                    Map.of("now", now, "id", groupId));
            audit.record(actor, "group", groupId, "close", "Group #" + groupId + " closed.", List.of("status"));
        }
    }

    private GroupRead read(Map<String, Object> row) {
        long id = RowValues.longValue(row, "id");
        long active = RowValues.longValue(row, "active_count");
        long max = RowValues.longValue(row, "max_members");
        String storedStatus = RowValues.requiredString(row, "status");
        String status = "closed".equals(storedStatus) ? storedStatus : active >= max ? "full" : "open";
        List<GroupMemberRead> members = repository.query(GroupQueries.READ_SELECT_01, Map.of("id", id)).stream().map(this::member).toList();
        boolean joinable = "open".equals(status) && active < max && RowValues.dateTime(row, "expires_at").isAfter(UtcDateTimes.now(clock));
        return GroupDtoMapper.group(row, members, status, joinable);
    }

    private GroupMemberRead member(Map<String, Object> row) {
        Long shipId = RowValues.nullableLong(row, "ship_id");
        ShipRead ship = shipId == null ? null : ships.activeShip(shipId);
        return GroupDtoMapper.member(row, ship);
    }

    private ResolvedSelection resolveSelection(GroupJoinRequest payload, AuthenticatedUser actor) {
        if (payload.buildId() != null) {
            Map<String, Object> row = repository.optional(GroupQueries.RESOLVE_SELECTION_SELECT_01, Map.of("buildId", payload.buildId(), "ownerId", actor.id()))
                    .orElseThrow(() -> bad("The selected build does not belong to your account."));
            return new ResolvedSelection(RowValues.longValue(row, "build_id"),
                    RowValues.longValue(row, "ship_id"), RowValues.requiredString(row, "ship_name"),
                    RowValues.nullableLong(row, "ship_rate"));
        }
        if (payload.shipId() != null) {
            Map<String, Object> row = repository.optional(GroupQueries.RESOLVE_SELECTION_SELECT_02, Map.of("id", payload.shipId()))
                    .orElseThrow(() -> bad("The selected ship does not exist."));
            return new ResolvedSelection(null, RowValues.longValue(row, "id"),
                    RowValues.requiredString(row, "name"), RowValues.nullableLong(row, "rate"));
        }
        return new ResolvedSelection(null, null, blank(payload.shipName()), payload.shipRate());
    }

    private static void validateRates(Long minRate, Long maxRate) {
        for (Long value : new Long[] {minRate, maxRate}) {
            if (value != null && (value < 1 || value > 7)) throw bad("Ship rate must be between 1 and 7.");
        }
        if (minRate != null && maxRate != null && maxRate > minRate) {
            throw bad("Maximum rate must be numerically lower than or equal to minimum rate.");
        }
    }

    private static void requireAllowedRate(Map<String, Object> group, Long rate) {
        Long min = RowValues.nullableLong(group, "min_ship_rate");
        Long max = RowValues.nullableLong(group, "max_ship_rate");
        if ((min != null || max != null) && rate == null) throw bad("This group requires a ship in the allowed range.");
        if (rate != null && ((min != null && rate > min) || (max != null && rate < max))) {
            throw bad("The selected ship is outside the allowed range.");
        }
    }

    private Map<String, Object> raw(long id) {
        return repository.optional(GroupQueries.GROUP_SELECT + GroupQueries.RAW_WHERE_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Group not found."));
    }

    private static String required(String value) {
        if (value == null || value.isBlank()) throw bad("A required text value is empty.");
        return value.strip();
    }

    private static String blank(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private record ResolvedSelection(Long buildId, Long shipId, String shipName, Long shipRate) { }
}
