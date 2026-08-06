// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record ProfilePreferenceOptionsRead(
        @NotNull @Size(max = 1000) List<ProfileShipOptionRead> ships,
        @NotNull @Size(max = 1000) List<ProfileRoleOptionRead> roles) { }
