package eu.royalblackwater.api.warehouse.service;

import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.warehouse.dto.WarehouseStockOverview;
import eu.royalblackwater.api.warehouse.repository.WarehouseRepository;
import eu.royalblackwater.api.warehouse.repository.queries.WarehouseQueries;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Builds the complete, concise stock snapshot used by fleet webhook subscribers. */
@Service
public class WarehouseOverviewService {
    private final WarehouseRepository repository;

    public WarehouseOverviewService(WarehouseRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public WarehouseStockOverview overview(long fleetId) {
        List<WarehouseStockOverview.Line> lines = repository.query(
                        WarehouseQueries.OVERVIEW_SELECT_01, java.util.Map.of("fleetId", fleetId))
                .stream()
                .map(row -> new WarehouseStockOverview.Line(
                        RowValues.requiredString(row, "port"), RowValues.requiredString(row, "resource"),
                        RowValues.longValue(row, "total"), RowValues.longValue(row, "available"),
                        RowValues.longValue(row, "reserved"), RowValues.requiredString(row, "collection_status"),
                        contact(row)))
                .toList();
        String fleetName = repository.optional(WarehouseQueries.FLEET_SELECT_01,
                        java.util.Map.of("fleetId", fleetId))
                .map(row -> RowValues.requiredString(row, "name"))
                .orElse("Fleet " + fleetId);
        return new WarehouseStockOverview(fleetName,
                lines.stream().mapToLong(WarehouseStockOverview.Line::total).sum(),
                lines.stream().mapToLong(WarehouseStockOverview.Line::available).sum(),
                lines.stream().mapToLong(WarehouseStockOverview.Line::reserved).sum(), lines);
    }

    public String format(WarehouseStockOverview overview) {
        StringBuilder output = new StringBuilder("Fleet: ").append(overview.fleetName())
                .append("\nTotal: ").append(overview.total())
                .append(" · Available: ").append(overview.available())
                .append(" · Reserved: ").append(overview.reserved());
        if (overview.lines().isEmpty()) return output.append("\n\nNo warehouse stock recorded.").toString();
        Map<String, Long> owned = new LinkedHashMap<>();
        for (WarehouseStockOverview.Line line : overview.lines()) {
            owned.merge(line.collectionStatus() + "\u0000" + line.contactName(), line.total(), Long::sum);
        }
        output.append("\n\nBy holder:");
        for (Map.Entry<String, Long> entry : owned.entrySet()) {
            String[] holder = entry.getKey().split("\u0000", 2);
            output.append("\n• ").append(holder[1]).append(" (").append(status(holder[0])).append("): ")
                    .append(entry.getValue());
        }
        output.append("\n\nBy port and resource:");
        for (WarehouseStockOverview.Line line : overview.lines()) {
            output.append("\n• ").append(line.port()).append(" · ").append(line.resource())
                    .append(": ").append(line.total()).append(" (available ")
                    .append(line.available()).append(", reserved ").append(line.reserved()).append(") · ")
                    .append(status(line.collectionStatus())).append(" · Holder: ")
                    .append(line.contactName());
        }
        return output.toString();
    }

    private static String contact(java.util.Map<String, Object> row) {
        String status = RowValues.requiredString(row, "collection_status");
        String key = "in_warehouse".equals(status) ? "assignee_name" : "donor_name";
        String contact = RowValues.string(row, key);
        return contact == null || contact.isBlank()
                ? ("in_warehouse".equals(status) ? "No port assignee assigned" : "Unknown donor")
                : contact;
    }

    private static String status(String collectionStatus) {
        return "in_warehouse".equals(collectionStatus) ? "Reached Guild-Warehouse" : "Awaiting collection";
    }
}
