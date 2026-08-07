// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public record MasterDataOptionRead(
        List<String> allowedSlotTypes,
        @Min(1) long categoryId,
        @NotNull String categoryKey,
        @NotNull String categoryLabel,
        @NotNull LocalDateTime createdAt,
        long id,
        String imageUrl,
        Boolean isActive,
        Boolean isSeedOverridden,
        @NotNull @Size(min = 1, max = 160) String name,
        String notes,
        String optionKind,
        String seedKey,
        String seedRevision,
        @NotNull String seedStatus,
        @Min(0) @Max(100000) Long sortOrder,
        String source,
        Map<String, Double> statEffects,
        @NotNull LocalDateTime updatedAt,
        Double weaponCaliberInches,
        String weaponClass,
        MasterDataWeaponPerformance weaponPerformance) { }
