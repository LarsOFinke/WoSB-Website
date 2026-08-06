// Generated API DTO by infrastructure/scripts/generation/generate_java_contracts.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;

public record BuildVoteState(
        long buildId,
        boolean hasUpvoted,
        @Min(0) long upvoteCount) { }
