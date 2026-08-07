// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Min;

public record MasterDataSeedRestoreSummary(
        @Min(0) long categories,
        Boolean customRecordsPreserved,
        @Min(0) long options,
        @Min(0) long overridesDiscarded,
        @Min(0) long ships,
        @Min(0) long total) { }
