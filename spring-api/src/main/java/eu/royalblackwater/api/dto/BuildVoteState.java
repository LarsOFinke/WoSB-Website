// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;

public record BuildVoteState(
        long buildId,
        boolean hasUpvoted,
        @Min(0) long upvoteCount) { }
