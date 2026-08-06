// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record MasterDataShipMount(
        @Min(0) @Max(1000) Long capacity,
        Double maxCaliberInches,
        String maxWeaponClass,
        @NotNull @Size(min = 1, max = 40) String slotType,
        @Min(0) @Max(1000) Long specialWeaponCapacity) { }
