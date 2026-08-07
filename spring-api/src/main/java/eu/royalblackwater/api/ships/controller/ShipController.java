package eu.royalblackwater.api.ships.controller;

import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.ships.filter.ShipListFilter;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ShipController extends ApiControllerSupport {
    private final ShipQueryService ships;

    public ShipController(ShipQueryService ships) { this.ships = ships; }

    @GetMapping("/api/ships")
    public ResponseEntity<List<ShipRead>> listShips(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "rate", required = false) Long rate,
            @RequestParam(name = "ship_type", required = false) String shipType,
            @RequestParam(name = "limit", defaultValue = "100") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        return respond(ships.activeShips(
                ShipListFilter.from(search, rate, shipType, limit, offset)), 200);
    }
}
