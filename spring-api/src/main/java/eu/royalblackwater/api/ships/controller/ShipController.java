package eu.royalblackwater.api.ships.controller;

import eu.royalblackwater.api.dto.ShipRead;
import java.util.List;
import eu.royalblackwater.api.contract.api.ShipsApi;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.ships.filter.ShipListFilter;
import eu.royalblackwater.api.ships.service.ShipQueryService;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ShipController extends ApiControllerSupport implements ShipsApi {
    private final ShipQueryService ships;

    public ShipController(ShipQueryService ships) { this.ships = ships; }

    @Override
    public ResponseEntity<List<ShipRead>> listShips(
            String search,
            Long rate,
            String shipType,
            long limit,
            long offset
    ) {
        return respond(ships.activeShips(
                ShipListFilter.from(search, rate, shipType, limit, offset)), 200);
    }
}
