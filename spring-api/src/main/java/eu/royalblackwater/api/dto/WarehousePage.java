// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record WarehousePage(
        long availableStock,
        @NotNull List<String> holders,
        @NotNull List<WarehouseEntryRead> items,
        long matchingStock,
        @NotNull List<String> ports,
        long reservedStock,
        @NotNull List<String> resources,
        long total) { }
