// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record FleetMembershipManagementRead(
        List<String> assignableRoles,
        Boolean canChangeRole,
        Boolean canChangeStatus,
        Boolean canEditDirectory,
        @JsonProperty("protected") Boolean protectedValue,
        String reason) { }
