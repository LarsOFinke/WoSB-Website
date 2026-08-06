package eu.royalblackwater.api.builds.dto;

import eu.royalblackwater.api.dto.WeaponPerformanceRead;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public record BuildCatalogOption(
        long id,
        String category,
        String name,
        String source,
        String notes,
        String imageUrl,
        String kind,
        String weaponClass,
        Integer weaponClassRank,
        Double caliber,
        int sortOrder,
        LocalDateTime createdAt,
        LocalDateTime updatedAt,
        List<String> allowedSlots,
        Map<String, Number> baseEffects,
        Map<String, Number> effects,
        boolean shipSpecific,
        WeaponPerformanceRead performance) { }
