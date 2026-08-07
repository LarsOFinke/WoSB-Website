// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record IpBlockSummary(
        Long active,
        Long expired,
        Long permanent,
        Long temporary,
        Long total,
        Long unblocked) { }
