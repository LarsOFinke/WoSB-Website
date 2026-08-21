package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehousePortCreate;
import eu.royalblackwater.api.dto.WarehousePortRead;
import eu.royalblackwater.api.dto.WarehousePortUpdate;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.mapper.WarehouseDtoMapper;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class WarehousePortService {
    private final WarehouseRepository repository;
    private final AuditService audit;
    private final Clock clock;

    public WarehousePortService(WarehouseRepository repository, AuditService audit, Clock clock) {
        this.repository = repository;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<WarehousePortRead> active(AuthenticatedUser actor) {
        requireAuthenticated(actor);
        return repository.query(WarehouseQueries.ACTIVE_PORTS_SELECT_01, Map.of()).stream()
                .map(WarehouseDtoMapper::port).toList();
    }

    @Transactional(readOnly = true)
    public List<WarehousePortRead> all(AuthenticatedUser actor) {
        requireAdmin(actor);
        return repository.query(WarehouseQueries.ALL_PORTS_SELECT_01, Map.of()).stream()
                .map(WarehouseDtoMapper::port).toList();
    }

    @Transactional
    public WarehousePortRead create(WarehousePortCreate payload, AuthenticatedUser actor) {
        requireAdmin(actor);
        String name = name(payload.name());
        requireUnique(null, name);
        long id = repository.insertReturningId(WarehouseQueries.CREATE_PORT_INSERT_01, Map.of(
                "name", name, "sortOrder", value(payload.sortOrder(), 100L),
                "active", value(payload.isActive(), true), "now", UtcDateTimes.now(clock)));
        audit.record(actor, "warehouse_port", id, "create", "Created warehouse port " + name,
                Set.of("name", "sort_order", "is_active"));
        return get(id);
    }

    @Transactional
    public WarehousePortRead update(long id, WarehousePortUpdate payload, AuthenticatedUser actor) {
        requireAdmin(actor);
        WarehousePortRead previous = get(id);
        String name = name(payload.name());
        requireUnique(id, name);
        LocalDateTime now = UtcDateTimes.now(clock);
        repository.update(WarehouseQueries.UPDATE_PORT_UPDATE_01, Map.of(
                "id", id, "name", name, "sortOrder", value(payload.sortOrder(), 100L),
                "active", value(payload.isActive(), true), "now", now));
        if (!previous.name().equals(name)) {
            repository.update(WarehouseQueries.RENAME_ENTRY_PORTS_UPDATE_01,
                    Map.of("name", name, "previousName", previous.name(), "now", now, "actorId", actor.id()));
        }
        audit.record(actor, "warehouse_port", id, "update", "Updated warehouse port " + name,
                Set.of("name", "sort_order", "is_active"));
        return get(id);
    }

    @Transactional
    public void deactivate(long id, AuthenticatedUser actor) {
        requireAdmin(actor);
        WarehousePortRead previous = get(id);
        repository.update(WarehouseQueries.DEACTIVATE_PORT_UPDATE_01, Map.of("id", id, "now", UtcDateTimes.now(clock)));
        audit.record(actor, "warehouse_port", id, "update", "Deactivated warehouse port " + previous.name(),
                Set.of("is_active"));
    }

    @Transactional(readOnly = true)
    public String requireActiveName(String raw) {
        String requested = name(raw);
        return repository.optional(WarehouseQueries.ACTIVE_PORT_BY_NAME_SELECT_01, Map.of("name", requested))
                .map(row -> RowValues.requiredString(row, "name"))
                .orElseThrow(() -> new ResponseStatusException(BAD_REQUEST, "Select an active warehouse port."));
    }

    private WarehousePortRead get(long id) {
        return repository.optional(WarehouseQueries.PORT_SELECT_01, Map.of("id", id))
                .map(WarehouseDtoMapper::port)
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Warehouse port not found."));
    }

    private void requireUnique(Long id, String name) {
        if (repository.count(WarehouseQueries.PORT_NAME_EXISTS_SELECT_01,
                SqlParameters.ofNullable("id", id, "name", name)) > 0) {
            throw new ResponseStatusException(CONFLICT, "A warehouse port with this name already exists.");
        }
    }

    private static String name(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new ResponseStatusException(BAD_REQUEST, "Port name is required.");
        }
        return raw.strip();
    }

    private static long value(Long value, long fallback) {
        return value == null ? fallback : value;
    }

    private static boolean value(Boolean value, boolean fallback) {
        return value == null ? fallback : value;
    }

    private static void requireAuthenticated(AuthenticatedUser actor) {
        if (actor == null) throw new ResponseStatusException(FORBIDDEN, "Warehouse access requires authentication.");
    }

    private static void requireAdmin(AuthenticatedUser actor) {
        if (actor == null || !actor.isAdmin()) {
            throw new ResponseStatusException(FORBIDDEN, "Warehouse port management requires administrator access.");
        }
    }
}
