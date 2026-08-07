// Generated API DTO by infrastructure/scripts/generation/generate_api_dtos.py; do not edit manually.
package eu.royalblackwater.api.dto;

import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record LegalNoticePublicRead(
        @Size(max = 4000) String additionalInformation,
        @Size(max = 120) String businessId,
        @Size(max = 120) String city,
        @Size(max = 120) String country,
        @Size(max = 4000) String disputeResolutionText,
        @Size(max = 120) String editorialResponsibleCity,
        @Size(max = 120) String editorialResponsibleCountry,
        @Size(max = 200) String editorialResponsibleName,
        @Size(max = 32) String editorialResponsiblePostalCode,
        @Size(max = 200) String editorialResponsibleStreet,
        @Size(max = 254) String email,
        @Size(max = 120) String legalForm,
        @Size(max = 80) String phone,
        @Size(max = 32) String postalCode,
        @Size(max = 200) String providerName,
        Boolean published,
        @Size(max = 200) String registerCourt,
        @Size(max = 160) String registerName,
        @Size(max = 120) String registerNumber,
        @Size(max = 300) String representedBy,
        @Size(max = 200) String street,
        @Size(max = 500) String supervisoryAuthority,
        LocalDateTime updatedAt,
        @Size(max = 80) String vatId) { }
