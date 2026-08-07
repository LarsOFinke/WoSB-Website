// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record WeaponClassRead(
        @NotNull String code,
        @NotNull String label,
        long rank) { }
