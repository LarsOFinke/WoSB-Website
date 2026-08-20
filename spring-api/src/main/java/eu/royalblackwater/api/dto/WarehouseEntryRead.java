// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record WarehouseEntryRead(
        long amount,
        @NotNull String collectionStatus,
        @NotNull LocalDateTime createdAt,
        String customHolderName,
        long fleetId,
        @NotNull String fleetName,
        @NotNull String holderName,
        long id,
        Long memberUserId,
        @NotNull String port,
        boolean reserved,
        @NotNull String resource,
        @NotNull LocalDateTime updatedAt,
        String portAssigneeName,
        Long portAssigneeUserId,
        String updatedBy,
        long version) { }
