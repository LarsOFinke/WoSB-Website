// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record LocalDatabaseBackup(
        String backupConsistency,
        @NotNull @Size(min = 64, max = 64) String backupId,
        Boolean backupSetVerified,
        Boolean checksumVerified,
        @NotNull String createdAt,
        Boolean encryptionKeysCompatible,
        @NotNull @Size(min = 1, max = 160) String filename,
        String flywayVersion,
        Boolean productionConsistent,
        Boolean restoreMetadataVerified,
        @NotNull @Size(min = 64, max = 64) String sha256,
        @Min(0) long sizeBytes) { }
