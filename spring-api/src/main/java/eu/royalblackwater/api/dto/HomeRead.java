// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record HomeRead(
        @NotNull @Size(min = 1, max = 128) String route,
        @NotNull @Size(min = 1, max = 160) String title,
        @NotNull @Size(min = 1, max = 128) String focus,
        @NotNull HomeActivityWindowRead activityWindow,
        @NotNull HomeVoicePolicyRead voicePolicy,
        @NotNull @Size(max = 32) List<HomeModuleRead> modules) { }
