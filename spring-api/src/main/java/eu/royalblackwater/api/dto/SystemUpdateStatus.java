// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record SystemUpdateStatus(
        String finishedAt,
        String message,
        String operation,
        Boolean requestAvailable,
        String requestedAt,
        String startedAt,
        String state) { }
