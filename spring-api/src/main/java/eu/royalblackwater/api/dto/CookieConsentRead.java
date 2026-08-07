// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record CookieConsentRead(
        Boolean analytics,
        LocalDateTime decidedAt,
        Boolean externalMedia,
        Boolean hasDecision,
        Boolean necessary,
        @NotNull String policyVersion,
        Boolean preferences) { }
