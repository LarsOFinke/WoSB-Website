// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record GuideUpdate(
        @NotNull @Size(min = 1, max = 20000) String body,
        @Size(max = 20) List<Long> buildIds,
        @Size(max = 80) String category,
        @Size(max = 20) List<Long> fileIds,
        String summary,
        @NotNull @Size(min = 1, max = 180) String title) { }
