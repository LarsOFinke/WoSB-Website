// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record MasterDataTaxonomyRead(
        List<ShipRateWeaponClassRuleRead> shipRateWeaponClasses,
        List<StatEffectDefinitionRead> statEffects,
        @NotNull List<WeaponClassRead> weaponClasses,
        @NotNull List<WeaponSlotTypeRead> weaponSlotTypes) { }
