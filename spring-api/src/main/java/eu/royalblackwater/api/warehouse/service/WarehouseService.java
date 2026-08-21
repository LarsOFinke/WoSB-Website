package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehouseEntryCreate;
import eu.royalblackwater.api.dto.WarehouseEntryRead;
import eu.royalblackwater.api.dto.WarehouseEntryUpdate;
import eu.royalblackwater.api.dto.WarehousePage;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.warehouse.mapper.WarehouseDtoMapper;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class WarehouseService {
    private final WarehouseRepository repository;
    private final WarehousePortService ports;
    private final WarehouseResourceService resources;
    private final AuditService audit;
    private final Clock clock;

    public WarehouseService(WarehouseRepository repository, WarehousePortService ports,
                            WarehouseResourceService resources, AuditService audit, Clock clock) {
        this.repository = repository;
        this.ports = ports;
        this.resources = resources;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public WarehousePage list(AuthenticatedUser actor, Long fleetId, String holder, String port,
                              String resource, Boolean reserved, long limit, long offset) {
        requireAuthenticated(actor);
        Long normalizedFleetId = ListFilter.optionalPositiveLong(fleetId, "fleet_id");
        ListFilter page = ListFilter.of(null, limit, offset, 500);
        Map<String, Object> parameters = new LinkedHashMap<>();
        String filters = filters(parameters, normalizedFleetId, holder, port, resource, reserved);
        parameters.put("limit", page.limit());
        parameters.put("offset", page.offset());

        List<WarehouseEntryRead> items = repository.query(
                        WarehouseQueries.ENTRY_SELECT + filters + WarehouseQueries.LIST_ORDER_LIMIT_01,
                        parameters).stream().map(WarehouseDtoMapper::entry).toList();
        Map<String, Object> summary = repository.required(WarehouseQueries.SUMMARY_SELECT + filters, parameters);
        Map<String, Object> facetParameters = SqlParameters.ofNullable("fleetId", normalizedFleetId);
        return WarehouseDtoMapper.page(summary, items,
                facets(WarehouseQueries.FACET_HOLDERS_SELECT_01, facetParameters),
                facets(WarehouseQueries.FACET_PORTS_SELECT_01, facetParameters),
                facets(WarehouseQueries.FACET_RESOURCES_SELECT_01, facetParameters));
    }

    @Transactional
    public WarehouseEntryRead create(WarehouseEntryCreate payload, AuthenticatedUser actor) {
        requireStaff(actor);
        requireFleet(payload.fleetId());
        Holder holder = resolveHolder(payload.fleetId(), payload.memberUserId(), payload.customHolderName());
        String port = ports.requireActiveName(payload.port());
        String collectionStatus = collectionStatus(payload.collectionStatus());
        LocalDateTime now = UtcDateTimes.now(clock);
        long id = repository.insertReturningId(WarehouseQueries.CREATE_INSERT_01, SqlParameters.ofNullable(
                "fleetId", payload.fleetId(), "memberUserId", holder.memberUserId(),
                "customHolderName", holder.customName(), "port", port,
                "resource", resources.requireActiveName(payload.resource()), "amount", payload.amount(),
                "reserved", Boolean.TRUE.equals(payload.reserved()), "collectionStatus", collectionStatus,
                "now", now, "actorId", actor.id()));
        WarehouseEntryRead created = get(id);
        audit.record(actor, "warehouse_entry", id, "create", stockCreatedSummary(created),
                List.of("fleet_id", "holder", "port", "resource", "amount", "reserved", "collection_status"),
                "fleet", created.fleetId());
        return created;
    }

    @Transactional
    public WarehouseEntryRead update(long id, WarehouseEntryUpdate payload, AuthenticatedUser actor) {
        requireStaff(actor);
        if (payload.version() < 1) throw bad("Version must be positive.");
        Map<String, Object> previous = raw(id);
        if (RowValues.longValue(previous, "version") != payload.version()) throw conflict();
        requireFleet(payload.fleetId());
        Holder holder = resolveHolder(payload.fleetId(), payload.memberUserId(), payload.customHolderName());
        String port = ports.requireActiveName(payload.port());
        String resource = resources.requireActiveName(payload.resource());
        String collectionStatus = collectionStatus(payload.collectionStatus());
        List<String> changed = changedFields(previous, payload, holder, port, resource, collectionStatus);
        if (changed.isEmpty()) return WarehouseDtoMapper.entry(previous);

        int updated = repository.update(WarehouseQueries.UPDATE_UPDATE_01, SqlParameters.ofNullable(
                "id", id, "version", payload.version(), "fleetId", payload.fleetId(),
                "memberUserId", holder.memberUserId(), "customHolderName", holder.customName(),
                "port", port, "resource", resource, "amount", payload.amount(),
                "reserved", payload.reserved(), "collectionStatus", collectionStatus,
                "now", UtcDateTimes.now(clock), "actorId", actor.id()));
        if (updated == 0) throw conflict();

        WarehouseEntryRead result = get(id);
        String action = changed.equals(List.of("reserved")) ? "reservation" : "update";
        String summary = "reservation".equals(action)
                ? reservationSummary(WarehouseDtoMapper.entry(previous), result)
                : stockUpdateSummary(WarehouseDtoMapper.entry(previous), result);
        audit.record(actor, "warehouse_entry", id, action, summary, changed, "fleet", result.fleetId());
        return result;
    }

    @Transactional
    public void delete(long id, long version, AuthenticatedUser actor) {
        requireStaff(actor);
        if (version < 1) throw bad("Version must be positive.");
        WarehouseEntryRead previous = WarehouseDtoMapper.entry(raw(id));
        if (repository.update(WarehouseQueries.DELETE_DELETE_01, Map.of("id", id, "version", version)) == 0) {
            throw conflict();
        }
        audit.record(actor, "warehouse_entry", id, "delete", stockDeletedSummary(previous),
                List.of("deleted"), "fleet", previous.fleetId());
    }

    private WarehouseEntryRead get(long id) {
        return WarehouseDtoMapper.entry(raw(id));
    }

    private Map<String, Object> raw(long id) {
        return repository.optional(WarehouseQueries.ENTRY_SELECT + WarehouseQueries.RAW_WHERE_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Warehouse entry not found."));
    }

    private String filters(Map<String, Object> parameters, Long fleetId, String holder, String port,
                           String resource, Boolean reserved) {
        StringBuilder sql = new StringBuilder(WarehouseQueries.FILTER_WHERE_01);
        if (fleetId != null) {
            sql.append(WarehouseQueries.FILTER_AND_FLEET_01);
            parameters.put("fleetId", fleetId);
        }
        appendTextFilter(sql, parameters, "holder", holder, WarehouseQueries.FILTER_AND_HOLDER_01);
        appendTextFilter(sql, parameters, "port", port, WarehouseQueries.FILTER_AND_PORT_01);
        appendTextFilter(sql, parameters, "resource", resource, WarehouseQueries.FILTER_AND_RESOURCE_01);
        if (reserved != null) {
            sql.append(WarehouseQueries.FILTER_AND_RESERVED_01);
            parameters.put("reserved", reserved);
        }
        return sql.toString();
    }

    private static void appendTextFilter(StringBuilder sql, Map<String, Object> parameters,
                                         String name, String raw, String fragment) {
        String value = ListFilter.optionalText(raw, name, 120);
        if (value == null) return;
        sql.append(fragment);
        parameters.put(name, value.toLowerCase(Locale.ROOT));
    }

    private List<String> facets(String sql, Map<String, Object> parameters) {
        return repository.query(sql, parameters).stream()
                .map(row -> RowValues.requiredString(row, "value"))
                .toList();
    }

    private void requireFleet(long fleetId) {
        if (fleetId < 1 || repository.optional(WarehouseQueries.FLEET_SELECT_01,
                Map.of("fleetId", fleetId)).isEmpty()) {
            throw bad("Select an active fleet.");
        }
    }

    private Holder resolveHolder(long fleetId, Long memberUserId, String customName) {
        String custom = optional(customName);
        if ((memberUserId == null) == (custom == null)) {
            throw bad("Select one fleet member or provide one custom holder name.");
        }
        if (memberUserId == null) return new Holder(null, custom);
        if (memberUserId < 1 || repository.optional(WarehouseQueries.MEMBER_SELECT_01,
                Map.of("fleetId", fleetId, "memberUserId", memberUserId)).isEmpty()) {
            throw bad("The selected account is not an active member of this fleet.");
        }
        return new Holder(memberUserId, null);
    }

    private static List<String> changedFields(Map<String, Object> previous, WarehouseEntryUpdate payload,
                                              Holder holder, String port, String resource, String collectionStatus) {
        List<String> changed = new ArrayList<>();
        changed(changed, "fleet_id", RowValues.longValue(previous, "fleet_id"), payload.fleetId());
        changed(changed, "holder", RowValues.nullableLong(previous, "member_user_id"), holder.memberUserId());
        changed(changed, "holder", RowValues.string(previous, "custom_holder_name"), holder.customName());
        changed(changed, "port", RowValues.requiredString(previous, "port"), port);
        changed(changed, "resource", RowValues.requiredString(previous, "resource"), resource);
        changed(changed, "amount", RowValues.longValue(previous, "amount"), payload.amount());
        changed(changed, "reserved", RowValues.booleanValue(previous, "reserved"), payload.reserved());
        changed(changed, "collection_status", RowValues.requiredString(previous, "collection_status"), collectionStatus);
        return changed.stream().distinct().toList();
    }

    private static void changed(List<String> fields, String name, Object before, Object after) {
        if (!Objects.equals(before, after)) fields.add(name);
    }

    private static String stockCreatedSummary(WarehouseEntryRead entry) {
        return "Warehouse stock created: " + description(entry) + " 0 → " + entry.amount()
                + status(entry.reserved()) + ".";
    }

    private static String stockUpdateSummary(WarehouseEntryRead before, WarehouseEntryRead after) {
        return "Warehouse stock updated: " + description(after) + " " + before.amount() + " → "
                + after.amount() + status(after.reserved()) + ".";
    }

    private static String reservationSummary(WarehouseEntryRead before, WarehouseEntryRead after) {
        return "Warehouse reservation changed: " + description(after) + " "
                + reservation(before.reserved()) + " → " + reservation(after.reserved()) + ".";
    }

    private static String stockDeletedSummary(WarehouseEntryRead entry) {
        return "Warehouse stock removed: " + description(entry) + " " + entry.amount() + " → 0.";
    }

    private static String description(WarehouseEntryRead entry) {
        return entry.holderName() + " · " + entry.port() + " · " + entry.resource();
    }

    private static String status(boolean reserved) {
        return " (" + reservation(reserved).toLowerCase(Locale.ROOT) + ")";
    }

    private static String reservation(boolean reserved) {
        return reserved ? "Reserved" : "Available";
    }

    private static String required(String value, String label) {
        String normalized = optional(value);
        if (normalized == null) throw bad(label + " is required.");
        return normalized;
    }

    private static String optional(String value) {
        return value == null || value.isBlank() ? null : value.strip();
    }

    private static String collectionStatus(String value) {
        String normalized = value == null || value.isBlank() ? "up_for_collection" : value.strip().toLowerCase(Locale.ROOT);
        if (!Set.of("up_for_collection", "in_warehouse").contains(normalized)) {
            throw bad("Collection status must be up_for_collection or in_warehouse.");
        }
        return normalized;
    }

    private static void requireAuthenticated(AuthenticatedUser actor) {
        if (actor == null) {
            throw new ResponseStatusException(FORBIDDEN, "Warehouse access requires authentication.");
        }
    }

    private static void requireStaff(AuthenticatedUser actor) {
        if (actor == null || !actor.staff()) {
            throw new ResponseStatusException(FORBIDDEN, "Warehouse changes require staff access.");
        }
    }

    private static ResponseStatusException bad(String message) {
        return new ResponseStatusException(BAD_REQUEST, message);
    }

    private static ResponseStatusException conflict() {
        return new ResponseStatusException(CONFLICT, "Warehouse entry changed; reload before saving again.");
    }

    private record Holder(Long memberUserId, String customName) { }
}
