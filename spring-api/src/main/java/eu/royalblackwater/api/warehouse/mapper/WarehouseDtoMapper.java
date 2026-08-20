package eu.royalblackwater.api.warehouse.mapper;

import eu.royalblackwater.api.dto.WarehouseEntryRead;
import eu.royalblackwater.api.dto.WarehousePage;
import eu.royalblackwater.api.dto.WarehousePortRead;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.List;
import java.util.Map;

/** Maps warehouse repository rows to the generated transport contract. */
public final class WarehouseDtoMapper {
    private WarehouseDtoMapper() { }

    public static WarehouseEntryRead entry(Map<String, Object> row) {
        return new WarehouseEntryRead(
                RowValues.longValue(row, "amount"),
                RowValues.dateTime(row, "created_at"),
                RowValues.string(row, "custom_holder_name"),
                RowValues.longValue(row, "fleet_id"),
                RowValues.requiredString(row, "fleet_name"),
                RowValues.requiredString(row, "holder_name"),
                RowValues.longValue(row, "id"),
                RowValues.nullableLong(row, "member_user_id"),
                RowValues.requiredString(row, "port"),
                RowValues.booleanValue(row, "reserved"),
                RowValues.requiredString(row, "resource"),
                RowValues.dateTime(row, "updated_at"),
                RowValues.string(row, "updated_by"),
                RowValues.longValue(row, "version"));
    }

    public static WarehousePage page(Map<String, Object> summary, List<WarehouseEntryRead> items,
                                     List<String> holders, List<String> ports, List<String> resources) {
        return new WarehousePage(
                RowValues.longValue(summary, "available_stock"),
                holders,
                items,
                RowValues.longValue(summary, "matching_stock"),
                ports,
                RowValues.longValue(summary, "reserved_stock"),
                resources,
                RowValues.longValue(summary, "total"));
    }

    public static WarehousePortRead port(Map<String, Object> row) {
        return new WarehousePortRead(
                RowValues.longValue(row, "id"),
                RowValues.requiredString(row, "name"),
                RowValues.longValue(row, "sort_order"),
                RowValues.booleanValue(row, "is_active"),
                RowValues.dateTime(row, "created_at"),
                RowValues.dateTime(row, "updated_at"));
    }
}
