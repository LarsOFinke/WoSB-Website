// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record BackupConnectionSummary(
        Boolean configured,
        String host,
        String hostKeyFingerprint,
        Boolean managedServer,
        Long port,
        Boolean privateKeyConfigured,
        String remoteDirectory,
        String uploadKeyFingerprint,
        String uploadPublicKey,
        String username,
        String writeTestedAt) { }
