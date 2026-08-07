// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record FleetUpdate(
        String description,
        String focus,
        Boolean isActive,
        String name,
        String slug,
        Long sortOrder,
        String standingOrders) { }
