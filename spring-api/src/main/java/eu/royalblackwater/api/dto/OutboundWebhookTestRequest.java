// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Size;

public record OutboundWebhookTestRequest(
        @Size(max = 80) String eventType) { }
