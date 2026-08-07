// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record NewcomerGuideResourceRead(
        Boolean available,
        String description,
        @NotNull String href,
        long id,
        @NotNull String label,
        Long resourceId,
        @NotNull String resourceType) { }
