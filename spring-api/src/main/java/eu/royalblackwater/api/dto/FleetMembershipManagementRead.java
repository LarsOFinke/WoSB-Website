// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import java.util.List;

public record FleetMembershipManagementRead(
        List<String> assignableRoles,
        Boolean canChangeRole,
        Boolean canChangeStatus,
        Boolean canEditDirectory,
        Boolean protectedValue,
        String reason) { }
