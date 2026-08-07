// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record BuildItemCategoryRead(
        long id,
        @NotNull String key,
        @NotNull String label,
        long sortOrder) { }
