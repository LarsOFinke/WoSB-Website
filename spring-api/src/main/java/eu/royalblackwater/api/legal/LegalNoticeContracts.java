package eu.royalblackwater.api.legal;

import java.time.LocalDateTime;

public final class LegalNoticeContracts {
    private LegalNoticeContracts() { }

    public record PublicRead(boolean published, String providerName, String legalForm, String representedBy,
                             String street, String postalCode, String city, String country, String email,
                             String phone, String registerName, String registerCourt, String registerNumber,
                             String vatId, String businessId, String supervisoryAuthority,
                             String editorialResponsibleName, String editorialResponsibleStreet,
                             String editorialResponsiblePostalCode, String editorialResponsibleCity,
                             String editorialResponsibleCountry, String disputeResolutionText,
                             String additionalInformation, LocalDateTime updatedAt) { }

    static PublicRead from(LegalNoticeEntity entity) {
        if (!entity.isPublished()) return unpublished(entity.getUpdatedAt());
        return new PublicRead(true, entity.getProviderName(), entity.getLegalForm(), entity.getRepresentedBy(),
                entity.getStreet(), entity.getPostalCode(), entity.getCity(), entity.getCountry(), entity.getEmail(),
                entity.getPhone(), entity.getRegisterName(), entity.getRegisterCourt(), entity.getRegisterNumber(),
                entity.getVatId(), entity.getBusinessId(), entity.getSupervisoryAuthority(),
                entity.getEditorialResponsibleName(), entity.getEditorialResponsibleStreet(),
                entity.getEditorialResponsiblePostalCode(), entity.getEditorialResponsibleCity(),
                entity.getEditorialResponsibleCountry(), entity.getDisputeResolutionText(),
                entity.getAdditionalInformation(), entity.getUpdatedAt());
    }

    static PublicRead unpublished(LocalDateTime updatedAt) {
        return new PublicRead(false, "", "", "", "", "", "", "Deutschland", "", "", "", "", "", "", "", "",
                "", "", "", "", "Deutschland", "", "", updatedAt);
    }
}
