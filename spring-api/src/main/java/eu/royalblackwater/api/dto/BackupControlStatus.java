// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import java.util.List;
import java.util.Map;

public record BackupControlStatus(
        Boolean ageRecipientConfigured,
        List<BackupArtifact> artifacts,
        BackupConnectionSummary connection,
        String discoveredFingerprint,
        String discoveredHost,
        String discoveredHostKey,
        Long discoveredPort,
        Boolean enrollmentApplied,
        String enrollmentId,
        String enrollmentPublicKey,
        Map<String, Object> enrollmentRequest,
        String finishedAt,
        String heartbeatAt,
        @Min(0) Long localCatalogSkippedCount,
        String localCatalogUpdatedAt,
        List<LocalDatabaseBackup> localDatabaseBackups,
        List<LocalFilesBackup> localFilesBackups,
        String message,
        String operation,
        Boolean requestAvailable,
        String requestedAt,
        String requestedBy,
        String startedAt,
        String state,
        String uploadKeyFingerprint,
        String uploadPublicKey) { }
