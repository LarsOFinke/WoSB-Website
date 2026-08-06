// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public record PersonalDataExportRead(
        @Min(1) long schemaVersion,
        @NotNull LocalDateTime exportedAt,
        @NotNull Map<String, Object> subject,
        @NotNull Map<String, List<Map<String, Object>>> categories,
        @NotNull @Size(max = 32) List<String> exclusions) { }
