package eu.royalblackwater.api.ships;

import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ShipOperationHandler extends AbstractApiOperationHandler {
    private final ShipQueryService ships;

    public ShipOperationHandler(ShipQueryService ships) { this.ships = ships; }

    @Override
    public Set<String> operations() { return Set.of("list_ships_api_ships_get"); }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return ships.activeShips(ShipListFilter.from(parameters));
    }
}
