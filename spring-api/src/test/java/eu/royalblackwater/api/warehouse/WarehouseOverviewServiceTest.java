package eu.royalblackwater.api.warehouse;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.warehouse.dto.WarehouseStockOverview;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.service.WarehouseOverviewService;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class WarehouseOverviewServiceTest {
    @Test
    void formatsFleetTotalsAndEveryPortResourceLine() {
        WarehouseStockOverview overview = new WarehouseStockOverview("Blackwater", 1_250, 1_000, 250,
                List.of(new WarehouseStockOverview.Line("Nassau", "Iron", 1_250, 1_000, 250,
                        "in_warehouse", "Harbor Master")));

        String message = new WarehouseOverviewService(new WarehouseRepository((JdbcQueryService) null)).format(overview);

        assertThat(message).contains("Fleet: Blackwater", "Total: 1250", "Available: 1000",
                "Reserved: 250", "By holder:", "Harbor Master (Reached Guild-Warehouse): 1250",
                "Nassau · Iron: 1250 (available 1000, reserved 250) · Reached Guild-Warehouse · Holder: Harbor Master");
    }

    @Test
    void usesDonorContactForStockAwaitingCollection() {
        WarehouseStockOverview overview = new WarehouseStockOverview("Blackwater", 500, 500, 0,
                List.of(new WarehouseStockOverview.Line("Nassau", "Iron", 500, 500, 0,
                        "up_for_collection", "Blackwater Donor")));

        String message = new WarehouseOverviewService(new WarehouseRepository((JdbcQueryService) null)).format(overview);

        assertThat(message).contains("Awaiting collection", "Holder: Blackwater Donor");
    }

    @Test
    void formatsEmptyFleetWithoutInventingStock() {
        WarehouseStockOverview overview = new WarehouseStockOverview("Blackwater", 0, 0, 0, List.of());

        String message = new WarehouseOverviewService(new WarehouseRepository((JdbcQueryService) null)).format(overview);

        assertThat(message).contains("No warehouse stock recorded.").doesNotContain("By port and resource");
    }
}
