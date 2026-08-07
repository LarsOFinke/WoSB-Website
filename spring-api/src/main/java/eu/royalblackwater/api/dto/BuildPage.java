// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import java.util.List;

public record BuildPage(
        List<BuildSummaryRead> items,
        Long limit,
        Long offset,
        Long total) { }
