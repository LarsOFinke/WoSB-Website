// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record PasswordChangeRequest(
        @NotNull @Size(min = 1, max = 200) String currentPassword,
        @NotNull @Size(min = 12, max = 200) String newPassword) { }
