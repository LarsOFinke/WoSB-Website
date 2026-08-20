// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record WarehousePortRead(
        long id,
        @NotNull String name,
        long sortOrder,
        boolean isActive,
        @NotNull LocalDateTime createdAt,
        @NotNull LocalDateTime updatedAt) { }
