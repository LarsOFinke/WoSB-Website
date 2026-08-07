// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record FleetRoleUpdate(
        Boolean canManageFleet,
        Boolean canManageMembers,
        Boolean isActive,
        Boolean isLeadership,
        String label,
        Long rank) { }
