package eu.royalblackwater.api.warehouse.controller;

import eu.royalblackwater.api.dto.WarehouseEntryCreate;
import eu.royalblackwater.api.dto.WarehouseEntryRead;
import eu.royalblackwater.api.dto.WarehouseEntryUpdate;
import eu.royalblackwater.api.dto.WarehousePage;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.warehouse.service.WarehouseService;
import jakarta.validation.Valid;
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

    public WarehouseController(WarehouseService warehouse) {
        this.warehouse = warehouse;
    }

    @GetMapping("/api/admin/warehouse")
    public ResponseEntity<WarehousePage> adminListWarehouseEntries(
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

    @PostMapping("/api/admin/warehouse")
    public ResponseEntity<WarehouseEntryRead> adminCreateWarehouseEntry(
            @Valid @RequestBody WarehouseEntryCreate body) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(warehouse.create(body, actor), 201);
    }

    @PutMapping("/api/admin/warehouse/{entry_id}")
    public ResponseEntity<WarehouseEntryRead> adminUpdateWarehouseEntry(
            @PathVariable("entry_id") long entryId,
            @Valid @RequestBody WarehouseEntryUpdate body) {
        return respond(warehouse.update(entryId, body, CurrentUser.require()), 200);
    }

    @DeleteMapping("/api/admin/warehouse/{entry_id}")
    public ResponseEntity<Void> adminDeleteWarehouseEntry(
            @PathVariable("entry_id") long entryId,
            @RequestParam(name = "version", required = true) long version) {
        warehouse.delete(entryId, version, CurrentUser.require());
        return noContent();
    }
}
