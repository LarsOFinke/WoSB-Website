// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record NewcomerGuideResourceInput(
        String description,
        String label,
        Long resourceId,
        @NotNull String resourceType,
        String url) { }
