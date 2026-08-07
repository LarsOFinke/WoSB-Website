// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record BuildRoleRead(
        @NotNull LocalDateTime createdAt,
        String description,
        @NotNull @Size(min = 1, max = 80) String label,
        @NotNull String slug,
        @Min(-10000) @Max(10000) Long sortOrder,
        @NotNull LocalDateTime updatedAt) { }
