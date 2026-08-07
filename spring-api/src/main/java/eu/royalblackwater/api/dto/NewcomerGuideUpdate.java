// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

public record NewcomerGuideUpdate(
        @Size(max = 30) List<NewcomerGuideBlockInput> blocks,
        @Size(max = 4000) String intro,
        @NotNull @Size(min = 1, max = 180) String title) { }
