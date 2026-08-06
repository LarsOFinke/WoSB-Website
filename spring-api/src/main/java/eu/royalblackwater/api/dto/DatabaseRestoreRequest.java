// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record DatabaseRestoreRequest(
        @NotNull String approvalToken,
        @NotNull @Size(min = 64, max = 64) String backupId,
        @NotNull String confirmation) { }
