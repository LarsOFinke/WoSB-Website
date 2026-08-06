package eu.royalblackwater.api.privacy.mapper;

import eu.royalblackwater.api.dto.CookieConsentPolicy;
import eu.royalblackwater.api.dto.CookieConsentRead;
import eu.royalblackwater.api.dto.DataSubjectRequestRead;
import eu.royalblackwater.api.dto.PersonalDataExportRead;
import eu.royalblackwater.api.dto.PrivacyContactRead;
import eu.royalblackwater.api.dto.PrivacyContactReceipt;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.privacy.entity.CookieConsentEntity;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class PrivacyDtoMapper {

    public static CookieConsentPolicy cookiePolicy(List<String> categories, String policyVersion) {
        return new CookieConsentPolicy(categories, policyVersion);
    }

    public static CookieConsentRead cookieConsent(CookieConsentEntity entity) {
        return new CookieConsentRead(entity.isAnalytics(), entity.getCreatedAt(), entity.isExternalMedia(),
                true, true, entity.getPolicyVersion(), entity.isPreferences());
    }

    public static CookieConsentRead emptyCookieConsent(String policyVersion) {
        return new CookieConsentRead(false, null, false, false, true, policyVersion, false);
    }
    public PrivacyContactReceipt contactReceipt(long id) {
        return new PrivacyContactReceipt(id, "pending");
    }

    public PrivacyContactRead contact(Map<String, Object> row) {
        return new PrivacyContactRead(RowValues.dateTime(row, "created_at"),
                RowValues.nullableLong(row, "handled_by_user_id"), RowValues.longValue(row, "id"),
                RowValues.requiredString(row, "message"), RowValues.requiredString(row, "reply_email"),
                RowValues.string(row, "resolution_note"), RowValues.nullableDateTime(row, "resolved_at"),
                RowValues.requiredString(row, "status"), RowValues.requiredString(row, "subject"),
                RowValues.nullableLong(row, "user_id"));
    }

    public PersonalDataExportRead personalDataExport(LocalDateTime exportedAt,
                                                     Map<String, Object> subject,
                                                     Map<String, List<Map<String, Object>>> categories,
                                                     List<String> exclusions) {
        return new PersonalDataExportRead(1, exportedAt, subject, categories, exclusions);
    }

    public DataSubjectRequestRead request(Map<String, Object> row) {
        return new DataSubjectRequestRead(
                RowValues.dateTime(row, "created_at"),
                (String) row.get("details"),
                nullableLong(row.get("handled_by_user_id")),
                RowValues.longValue(row, "id"),
                RowValues.string(row, "request_type"),
                (String) row.get("resolution_note"),
                RowValues.nullableDateTime(row, "resolved_at"),
                RowValues.string(row, "status"),
                RowValues.longValue(row, "subject_user_id"),
                (String) row.get("subject_username"));
    }

    private static Long nullableLong(Object value) {
        return value instanceof Number number ? number.longValue() : null;
    }
}
