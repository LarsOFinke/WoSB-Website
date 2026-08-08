// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record BuildPrintoutRead(
        boolean changed,
        @NotNull @Size(max = 128) String cacheKey,
        @NotNull String checksum,
        long sizeBytes,
        @NotNull LocalDateTime sourceUpdatedAt,
        @NotNull LocalDateTime updatedAt,
        @NotNull String url) { }
