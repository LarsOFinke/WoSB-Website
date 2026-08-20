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
                List.of(new WarehouseStockOverview.Line("Nassau", "Iron", 1_250, 1_000, 250)));

        String message = new WarehouseOverviewService(new WarehouseRepository((JdbcQueryService) null)).format(overview);

        assertThat(message).contains("Fleet: Blackwater", "Total: 1250", "Available: 1000",
                "Reserved: 250", "Nassau · Iron: 1250 (available 1000, reserved 250)");
    }

    @Test
    void formatsEmptyFleetWithoutInventingStock() {
        WarehouseStockOverview overview = new WarehouseStockOverview("Blackwater", 0, 0, 0, List.of());

        String message = new WarehouseOverviewService(new WarehouseRepository((JdbcQueryService) null)).format(overview);

        assertThat(message).contains("No warehouse stock recorded.").doesNotContain("By port and resource");
    }
}
