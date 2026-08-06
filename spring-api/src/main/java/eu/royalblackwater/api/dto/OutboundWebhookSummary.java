// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record OutboundWebhookSummary(
        Long active,
        Long failedDeliveries,
        Long failing,
        Long successfulDeliveries,
        Long total) { }
