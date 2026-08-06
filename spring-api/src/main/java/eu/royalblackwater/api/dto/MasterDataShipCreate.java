// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record MasterDataShipCreate(
        @Min(0) Double armor,
        @Min(0) Long crewCapacity,
        @Min(0) Long displacementTons,
        @Min(0) Long durability,
        Boolean hasLantern,
        @Min(0) Long holdCapacity,
        String imageUrl,
        Boolean isActive,
        @Min(0) Double maneuverability,
        MasterDataShipMortarModification mortarModification,
        @NotNull @Size(min = 1, max = 120) String name,
        @Min(1) @Max(7) long rate,
        @Min(0) @Max(20) Long sailSlots,
        @Min(0) Long sailorMinimum,
        @NotNull @Size(min = 1, max = 80) String shipType,
        String source,
        @Min(0) Double speedKnots,
        @Min(0) Double speedMinKnots,
        List<MasterDataShipUpgradeOverride> upgradeEffectOverrides,
        @Min(0) @Max(8) Long upgradeSlots,
        List<MasterDataShipMount> weaponMounts) { }
