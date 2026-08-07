// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record BackupEnrollmentResponseRequest(
        @NotNull @Size(min = 2, max = 32768) String responseJson) { }
