// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record WarehousePortAssignmentRead(
        String assigneeName,
        Long assigneeUserId,
        long fleetId,
        @NotNull String fleetName,
        long portId,
        @NotNull String portName,
        @NotNull LocalDateTime updatedAt) { }
