// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record MasterDataCategoryRead(
        @NotNull LocalDateTime createdAt,
        long id,
        Boolean isActive,
        Boolean isSeedOverridden,
        @NotNull String key,
        @NotNull @Size(min = 1, max = 80) String label,
        String seedKey,
        String seedRevision,
        @NotNull String seedStatus,
        @Min(0) @Max(100000) Long sortOrder,
        @NotNull LocalDateTime updatedAt) { }
