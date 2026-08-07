// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record FilesRestoreRequest(
        @NotNull String approvalToken,
        @NotNull @Size(min = 64, max = 64) String backupId,
        @NotNull @Size(min = 1, max = 3) List<String> components,
        @NotNull String confirmation) { }
