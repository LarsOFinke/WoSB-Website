// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record BuildListMetrics(
        Long ammunitionSlotsUsed,
        Long consumableSlotsUsed,
        Long crewCapacity,
        Long crewTotal,
        Long holdSlotsUsed,
        Long specialCrewTotal,
        Long upgradeSlotsAvailable,
        Long upgradeSlotsUsed,
        Long weaponTotal) { }
