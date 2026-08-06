package eu.royalblackwater.api.legal.mapper;

import eu.royalblackwater.api.config.LegalNoticeProperties;
import eu.royalblackwater.api.dto.LegalNoticeAdminRead;
import eu.royalblackwater.api.dto.LegalNoticePublicRead;
import eu.royalblackwater.api.dto.LegalNoticeUpdate;
import eu.royalblackwater.api.persistence.RowValues;
import java.time.LocalDateTime;
import java.util.Map;

public final class LegalNoticeDtoMapper {
    private LegalNoticeDtoMapper() { }

    public static LegalNoticeUpdate environmentUpdate(LegalNoticeProperties source) {
        return new LegalNoticeUpdate(source.additionalInformation(), source.businessId(), source.city(),
                source.country(), source.disputeResolutionText(), source.editorialResponsibleCity(),
                source.editorialResponsibleCountry(), source.editorialResponsibleName(),
                source.editorialResponsiblePostalCode(), source.editorialResponsibleStreet(), source.email(),
                source.legalForm(), source.phone(), source.postalCode(), source.providerName(), source.published(),
                source.registerCourt(), source.registerName(), source.registerNumber(), source.representedBy(),
                source.street(), source.supervisoryAuthority(), source.vatId());
    }

    public static LegalNoticeAdminRead admin(Map<String, Object> row) {
        return new LegalNoticeAdminRead(s(row, "additional_information"), s(row, "business_id"),
                s(row, "city"), s(row, "country"), s(row, "dispute_resolution_text"),
                s(row, "editorial_responsible_city"), s(row, "editorial_responsible_country"),
                s(row, "editorial_responsible_name"), s(row, "editorial_responsible_postal_code"),
                s(row, "editorial_responsible_street"), s(row, "email"), s(row, "legal_form"),
                s(row, "phone"), s(row, "postal_code"), s(row, "provider_name"),
                RowValues.booleanValue(row, "published"), s(row, "register_court"),
                s(row, "register_name"), s(row, "register_number"), s(row, "represented_by"),
                RowValues.booleanValue(row, "is_customized") ? "admin" : "environment", s(row, "street"),
                s(row, "supervisory_authority"), RowValues.dateTime(row, "updated_at"),
                s(row, "updated_by_username"), s(row, "vat_id"));
    }

    public static LegalNoticePublicRead published(Map<String, Object> row) {
        return new LegalNoticePublicRead(s(row, "additional_information"), s(row, "business_id"),
                s(row, "city"), s(row, "country"), s(row, "dispute_resolution_text"),
                s(row, "editorial_responsible_city"), s(row, "editorial_responsible_country"),
                s(row, "editorial_responsible_name"), s(row, "editorial_responsible_postal_code"),
                s(row, "editorial_responsible_street"), s(row, "email"), s(row, "legal_form"),
                s(row, "phone"), s(row, "postal_code"), s(row, "provider_name"), true,
                s(row, "register_court"), s(row, "register_name"), s(row, "register_number"),
                s(row, "represented_by"), s(row, "street"), s(row, "supervisory_authority"),
                RowValues.dateTime(row, "updated_at"), s(row, "vat_id"));
    }

    public static LegalNoticePublicRead unpublished(LocalDateTime updatedAt) {
        return new LegalNoticePublicRead(null, null, null, null, null, null, null, null, null, null,
                null, null, null, null, null, false, null, null, null, null, null, null, updatedAt, null);
    }

    private static String s(Map<String, Object> row, String key) {
        return RowValues.string(row, key);
    }
}
