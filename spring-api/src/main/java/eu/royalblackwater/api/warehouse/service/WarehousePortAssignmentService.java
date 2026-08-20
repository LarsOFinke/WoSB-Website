package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.WarehousePortAssignmentRead;
import eu.royalblackwater.api.dto.WarehousePortAssignmentUpdate;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.mapper.WarehouseDtoMapper;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class WarehousePortAssignmentService {
    private final WarehouseRepository repository;
    private final AuditService audit;
    private final Clock clock;

    public WarehousePortAssignmentService(WarehouseRepository repository, AuditService audit, Clock clock) {
        this.repository = repository;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<WarehousePortAssignmentRead> list(long fleetId, AuthenticatedUser actor) {
        requireFleetAccess(fleetId, actor);
        return repository.query(WarehouseQueries.ASSIGNMENTS_SELECT_01 + WarehouseQueries.ASSIGNMENTS_ORDER_BY_01,
                        Map.of("fleetId", fleetId)).stream().map(WarehouseDtoMapper::assignment).toList();
    }

    @Transactional
    public WarehousePortAssignmentRead update(long portId, WarehousePortAssignmentUpdate input,
                                              AuthenticatedUser actor) {
        requireStaff(actor);
        if (portId < 1) throw bad("Port is required.");
        requireFleet(input.fleetId());
        if (repository.count(WarehouseQueries.ACTIVE_PORT_BY_ID_SELECT_01,
                Map.of("portId", portId)) == 0) throw notFound("Warehouse port");
        if (input.assigneeUserId() != null && repository.count(WarehouseQueries.ACTIVE_FLEET_MEMBER_SELECT_01,
                Map.of("fleetId", input.fleetId(), "userId", input.assigneeUserId())) == 0) {
            throw bad("The pickup assignee must be an active member of this fleet.");
        }
        repository.update(WarehouseQueries.ASSIGNMENT_UPSERT_01, SqlParameters.ofNullable(
                "fleetId", input.fleetId(), "portId", portId, "assigneeUserId", input.assigneeUserId(),
                "now", now(), "actorId", actor.id()));
        audit.record(actor, "warehouse_port_assignment", input.fleetId(), "update",
                "Updated warehouse pickup assignment for port #" + portId + ".",
                List.of("fleet_id", "port_id", "assignee_user_id"), "fleet", input.fleetId());
        return repository.optional(WarehouseQueries.ASSIGNMENT_SELECT_01,
                        Map.of("fleetId", input.fleetId(), "portId", portId))
                .map(WarehouseDtoMapper::assignment)
                .orElseThrow(() -> notFound("Warehouse port assignment"));
    }

    private void requireFleetAccess(long fleetId, AuthenticatedUser actor) {
        if (actor == null) throw new ResponseStatusException(FORBIDDEN, "Warehouse access requires authentication.");
        requireFleet(fleetId);
        if (actor.staff()) return;
        if (repository.count(WarehouseQueries.ACTIVE_FLEET_MEMBER_SELECT_01,
                Map.of("fleetId", fleetId, "userId", actor.id())) == 0) {
            throw new ResponseStatusException(FORBIDDEN, "You are not a member of this fleet.");
        }
    }

    private void requireFleet(long fleetId) {
        if (fleetId < 1 || repository.optional(WarehouseQueries.FLEET_SELECT_01,
                Map.of("fleetId", fleetId)).isEmpty()) throw notFound("Fleet");
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static void requireStaff(AuthenticatedUser actor) {
        if (actor == null || !actor.staff()) throw new ResponseStatusException(FORBIDDEN, "Warehouse changes require staff access.");
    }

    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException notFound(String subject) { return new ResponseStatusException(NOT_FOUND, subject + " not found."); }
}
