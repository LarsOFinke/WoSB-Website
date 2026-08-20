package eu.royalblackwater.api.warehouse.dto;

import java.util.List;

/** Internal, fleet-scoped stock snapshot used by member-facing webhook messages. */
public record WarehouseStockOverview(
        String fleetName,
        long total,
        long available,
        long reserved,
        List<Line> lines) {

    public record Line(String port, String resource, long total, long available, long reserved) { }
}
