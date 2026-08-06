// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record FleetUpdate(
        String description,
        String focus,
        Boolean isActive,
        String name,
        String slug,
        Long sortOrder,
        String standingOrders) { }
