// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

public record IpBlockSummary(
        Long active,
        Long expired,
        Long permanent,
        Long temporary,
        Long total,
        Long unblocked) { }
