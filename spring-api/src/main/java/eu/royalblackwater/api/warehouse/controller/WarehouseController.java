package eu.royalblackwater.api.warehouse.controller;

import eu.royalblackwater.api.dto.WarehouseEntryCreate;
import eu.royalblackwater.api.dto.WarehouseEntryRead;
import eu.royalblackwater.api.dto.WarehouseEntryUpdate;
import eu.royalblackwater.api.dto.WarehousePage;
import eu.royalblackwater.api.dto.WarehousePortCreate;
import eu.royalblackwater.api.dto.WarehousePortAssignmentRead;
import eu.royalblackwater.api.dto.WarehousePortAssignmentUpdate;
import eu.royalblackwater.api.dto.WarehousePortRead;
import eu.royalblackwater.api.dto.WarehousePortUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.warehouse.service.WarehouseService;
import eu.royalblackwater.api.warehouse.service.WarehousePortService;
import eu.royalblackwater.api.warehouse.service.WarehousePortAssignmentService;
import eu.royalblackwater.api.warehouse.service.WarehouseOverviewWebhookService;
import jakarta.validation.Valid;
import java.util.List;
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
public class WarehouseController extends ApiControllerSupport {
    private final WarehouseService warehouse;
    private final WarehousePortService ports;
    private final WarehousePortAssignmentService assignments;
    private final WarehouseOverviewWebhookService overviewWebhook;

    public WarehouseController(WarehouseService warehouse, WarehousePortService ports,
                               WarehousePortAssignmentService assignments,
                               WarehouseOverviewWebhookService overviewWebhook) {
        this.warehouse = warehouse;
        this.ports = ports;
        this.assignments = assignments;
        this.overviewWebhook = overviewWebhook;
    }

    @GetMapping("/api/warehouse")
    public ResponseEntity<WarehousePage> listWarehouseEntries(
            @RequestParam(name = "fleet_id", required = false) Long fleetId,
            @RequestParam(name = "holder", required = false) String holder,
            @RequestParam(name = "port", required = false) String port,
            @RequestParam(name = "resource", required = false) String resource,
            @RequestParam(name = "reserved", required = false) Boolean reserved,
            @RequestParam(name = "limit", defaultValue = "100") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset) {
        return respond(warehouse.list(CurrentUser.require(), fleetId, holder, port, resource,
                reserved, limit, offset), 200);
    }

    @PostMapping("/api/warehouse")
    public ResponseEntity<WarehouseEntryRead> createWarehouseEntry(
            @Valid @RequestBody WarehouseEntryCreate body) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(warehouse.create(body, actor), 201);
    }

    @PutMapping("/api/warehouse/{entry_id}")
    public ResponseEntity<WarehouseEntryRead> updateWarehouseEntry(
            @PathVariable("entry_id") long entryId,
            @Valid @RequestBody WarehouseEntryUpdate body) {
        return respond(warehouse.update(entryId, body, CurrentUser.require()), 200);
    }

    @DeleteMapping("/api/warehouse/{entry_id}")
    public ResponseEntity<Void> deleteWarehouseEntry(
            @PathVariable("entry_id") long entryId,
            @RequestParam(name = "version", required = true) long version) {
        warehouse.delete(entryId, version, CurrentUser.require());
        return noContent();
    }

    @GetMapping("/api/warehouse/ports")
    public ResponseEntity<List<WarehousePortRead>> listWarehousePorts() {
        return respond(ports.active(CurrentUser.require()), 200);
    }

    @GetMapping("/api/warehouse/port-assignments")
    public ResponseEntity<List<WarehousePortAssignmentRead>> listWarehousePortAssignments(
            @RequestParam(name = "fleet_id", required = true) long fleetId) {
        return respond(assignments.list(fleetId, CurrentUser.require()), 200);
    }

    @PutMapping("/api/warehouse/port-assignments/{port_id}")
    public ResponseEntity<WarehousePortAssignmentRead> updateWarehousePortAssignment(
            @PathVariable("port_id") long portId,
            @Valid @RequestBody WarehousePortAssignmentUpdate body) {
        return respond(assignments.update(portId, body, CurrentUser.require()), 200);
    }

    @PostMapping("/api/warehouse/overview/webhook")
    public ResponseEntity<Void> publishWarehouseOverviewWebhook(
            @RequestParam(name = "fleet_id", required = true) long fleetId) {
        overviewWebhook.publish(fleetId, CurrentUser.require());
        return noContent();
    }

    @GetMapping("/api/admin/master-data/warehouse-ports")
    public ResponseEntity<List<WarehousePortRead>> listAdminWarehousePorts() {
        return respond(ports.all(CurrentUser.require()), 200);
    }

    @PostMapping("/api/admin/master-data/warehouse-ports")
    public ResponseEntity<WarehousePortRead> createWarehousePort(
            @Valid @RequestBody WarehousePortCreate body) {
        return respond(ports.create(body, CurrentUser.require()), 201);
    }

    @PutMapping("/api/admin/master-data/warehouse-ports/{port_id}")
    public ResponseEntity<WarehousePortRead> updateWarehousePort(
            @PathVariable("port_id") long portId,
            @Valid @RequestBody WarehousePortUpdate body) {
        return respond(ports.update(portId, body, CurrentUser.require()), 200);
    }

    @DeleteMapping("/api/admin/master-data/warehouse-ports/{port_id}")
    public ResponseEntity<Void> deactivateWarehousePort(@PathVariable("port_id") long portId) {
        ports.deactivate(portId, CurrentUser.require());
        return noContent();
    }
}
