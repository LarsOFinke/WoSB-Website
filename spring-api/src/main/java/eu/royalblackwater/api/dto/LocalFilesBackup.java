// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record LocalFilesBackup(
        @NotNull @Size(min = 64, max = 64) String backupId,
        Boolean checksumVerified,
        List<String> components,
        @NotNull String createdAt,
        @NotNull @Size(min = 1, max = 160) String filename,
        @NotNull @Size(min = 64, max = 64) String sha256,
        @Min(0) long sizeBytes) { }
