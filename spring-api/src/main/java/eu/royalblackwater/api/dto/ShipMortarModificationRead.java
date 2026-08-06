// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;

public record ShipMortarModificationRead(
        long broadsideCapacityDelta,
        long crewCapacityDelta,
        long durabilityDelta,
        double holdCapacityPct,
        double maneuverabilityDelta,
        double maxCaliberInches,
        long mortarCapacity,
        @NotNull String source,
        double speedPct) { }
