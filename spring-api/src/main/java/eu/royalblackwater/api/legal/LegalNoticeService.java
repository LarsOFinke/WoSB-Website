package eu.royalblackwater.api.legal;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.config.LegalNoticeProperties;
import eu.royalblackwater.api.contract.LegalNoticeAdminRead;
import eu.royalblackwater.api.contract.LegalNoticePublicRead;
import eu.royalblackwater.api.contract.LegalNoticeUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LegalNoticeService {
    private static final int ID = 1;
    private final JdbcQueryService jdbc;
    private final LegalNoticeProperties environment;
    private final AuditService audit;
    private final Clock clock;

    public LegalNoticeService(JdbcQueryService jdbc, LegalNoticeProperties environment,
                              AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.environment = environment;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public LegalNoticePublicRead publicNotice() {
        Map<String, Object> row = row().orElse(null);
        if (row == null || !RowValues.booleanValue(row, "published")) {
            return new LegalNoticePublicRead(null, null, null, null, null, null, null, null, null, null,
                    null, null, null, null, null, false, null, null, null, null, null, null,
                    row == null ? null : RowValues.dateTime(row, "updated_at"), null);
        }
        return publicRead(row);
    }

    @Transactional
    public LegalNoticeAdminRead adminNotice() {
        ensureEnvironmentRow();
        return adminRead(requiredRow());
    }

    @Transactional
    public LegalNoticeAdminRead update(LegalNoticeUpdate payload, AuthenticatedUser actor) {
        ensureEnvironmentRow();
        Map<String, Object> previous = requiredRow();
        Map<String, Object> values = payloadValues(payload, true, actor.username());
        jdbc.update(updateSql(), values);
        audit.record(actor, "legal_notice", ID, "update", "Impressum settings updated.",
                changedFields(previous, values));
        return adminRead(requiredRow());
    }

    @Transactional
    public LegalNoticeAdminRead reset(AuthenticatedUser actor) {
        ensureEnvironmentRow();
        Map<String, Object> previous = requiredRow();
        Map<String, Object> values = environmentValues(false, "environment");
        jdbc.update(updateSql(), values);
        audit.record(actor, "legal_notice", ID, "restore",
                "Impressum settings restored from environment configuration.",
                changedFields(previous, values));
        return adminRead(requiredRow());
    }

    private void ensureEnvironmentRow() {
        Map<String, Object> values = environmentValues(false, "environment");
        jdbc.update("""
                insert into legal_notices(
                    id,published,is_customized,provider_name,legal_form,represented_by,street,postal_code,
                    city,country,email,phone,register_name,register_court,register_number,vat_id,business_id,
                    supervisory_authority,editorial_responsible_name,editorial_responsible_street,
                    editorial_responsible_postal_code,editorial_responsible_city,editorial_responsible_country,
                    dispute_resolution_text,additional_information,updated_by_username,updated_at)
                values(1,:published,:customized,:providerName,:legalForm,:representedBy,:street,:postalCode,
                    :city,:country,:email,:phone,:registerName,:registerCourt,:registerNumber,:vatId,:businessId,
                    :supervisoryAuthority,:editorialResponsibleName,:editorialResponsibleStreet,
                    :editorialResponsiblePostalCode,:editorialResponsibleCity,:editorialResponsibleCountry,
                    :disputeResolutionText,:additionalInformation,:updatedBy,:updatedAt)
                on conflict(id) do nothing
                """, values);
    }

    private java.util.Optional<Map<String, Object>> row() {
        return jdbc.optional("select * from legal_notices where id=:id", Map.of("id", ID));
    }

    private Map<String, Object> requiredRow() {
        return row().orElseThrow(() -> new IllegalStateException("Legal notice singleton is missing."));
    }

    private Map<String, Object> payloadValues(LegalNoticeUpdate p, boolean customized, String updatedBy) {
        return SqlParameters.ofNullable(
                "id", ID, "published", Boolean.TRUE.equals(p.published()), "customized", customized,
                "providerName", value(p.providerName()), "legalForm", value(p.legalForm()),
                "representedBy", value(p.representedBy()), "street", value(p.street()),
                "postalCode", value(p.postalCode()), "city", value(p.city()), "country", value(p.country()),
                "email", value(p.email()), "phone", value(p.phone()), "registerName", value(p.registerName()),
                "registerCourt", value(p.registerCourt()), "registerNumber", value(p.registerNumber()),
                "vatId", value(p.vatId()), "businessId", value(p.businessId()),
                "supervisoryAuthority", value(p.supervisoryAuthority()),
                "editorialResponsibleName", value(p.editorialResponsibleName()),
                "editorialResponsibleStreet", value(p.editorialResponsibleStreet()),
                "editorialResponsiblePostalCode", value(p.editorialResponsiblePostalCode()),
                "editorialResponsibleCity", value(p.editorialResponsibleCity()),
                "editorialResponsibleCountry", value(p.editorialResponsibleCountry()),
                "disputeResolutionText", value(p.disputeResolutionText()),
                "additionalInformation", value(p.additionalInformation()), "updatedBy", updatedBy,
                "updatedAt", now());
    }

    private Map<String, Object> environmentValues(boolean customized, String updatedBy) {
        return payloadValues(new LegalNoticeUpdate(environment.additionalInformation(), environment.businessId(),
                environment.city(), environment.country(), environment.disputeResolutionText(),
                environment.editorialResponsibleCity(), environment.editorialResponsibleCountry(),
                environment.editorialResponsibleName(), environment.editorialResponsiblePostalCode(),
                environment.editorialResponsibleStreet(), environment.email(), environment.legalForm(),
                environment.phone(), environment.postalCode(), environment.providerName(), environment.published(),
                environment.registerCourt(), environment.registerName(), environment.registerNumber(),
                environment.representedBy(), environment.street(), environment.supervisoryAuthority(),
                environment.vatId()), customized, updatedBy);
    }

    private String updateSql() {
        return """
                update legal_notices set published=:published,is_customized=:customized,
                    provider_name=:providerName,legal_form=:legalForm,represented_by=:representedBy,
                    street=:street,postal_code=:postalCode,city=:city,country=:country,email=:email,phone=:phone,
                    register_name=:registerName,register_court=:registerCourt,register_number=:registerNumber,
                    vat_id=:vatId,business_id=:businessId,supervisory_authority=:supervisoryAuthority,
                    editorial_responsible_name=:editorialResponsibleName,
                    editorial_responsible_street=:editorialResponsibleStreet,
                    editorial_responsible_postal_code=:editorialResponsiblePostalCode,
                    editorial_responsible_city=:editorialResponsibleCity,
                    editorial_responsible_country=:editorialResponsibleCountry,
                    dispute_resolution_text=:disputeResolutionText,additional_information=:additionalInformation,
                    updated_by_username=:updatedBy,updated_at=:updatedAt where id=:id
                """;
    }

    private static LegalNoticeAdminRead adminRead(Map<String, Object> r) {
        return new LegalNoticeAdminRead(s(r,"additional_information"),s(r,"business_id"),s(r,"city"),s(r,"country"),
                s(r,"dispute_resolution_text"),s(r,"editorial_responsible_city"),
                s(r,"editorial_responsible_country"),s(r,"editorial_responsible_name"),
                s(r,"editorial_responsible_postal_code"),s(r,"editorial_responsible_street"),s(r,"email"),
                s(r,"legal_form"),s(r,"phone"),s(r,"postal_code"),s(r,"provider_name"),
                RowValues.booleanValue(r,"published"),s(r,"register_court"),s(r,"register_name"),
                s(r,"register_number"),s(r,"represented_by"),
                RowValues.booleanValue(r,"is_customized") ? "admin" : "environment",s(r,"street"),
                s(r,"supervisory_authority"),RowValues.dateTime(r,"updated_at"),
                s(r,"updated_by_username"),s(r,"vat_id"));
    }

    private static LegalNoticePublicRead publicRead(Map<String, Object> r) {
        return new LegalNoticePublicRead(s(r,"additional_information"),s(r,"business_id"),s(r,"city"),s(r,"country"),
                s(r,"dispute_resolution_text"),s(r,"editorial_responsible_city"),
                s(r,"editorial_responsible_country"),s(r,"editorial_responsible_name"),
                s(r,"editorial_responsible_postal_code"),s(r,"editorial_responsible_street"),s(r,"email"),
                s(r,"legal_form"),s(r,"phone"),s(r,"postal_code"),s(r,"provider_name"),true,
                s(r,"register_court"),s(r,"register_name"),s(r,"register_number"),s(r,"represented_by"),
                s(r,"street"),s(r,"supervisory_authority"),RowValues.dateTime(r,"updated_at"),s(r,"vat_id"));
    }

    private static List<String> changedFields(Map<String, Object> previous, Map<String, Object> next) {
        List<String> changed = new ArrayList<>();
        Map<String, String> columns = Map.ofEntries(
                Map.entry("published","published"),Map.entry("customized","is_customized"),
                Map.entry("providerName","provider_name"),Map.entry("legalForm","legal_form"),
                Map.entry("representedBy","represented_by"),Map.entry("street","street"),
                Map.entry("postalCode","postal_code"),Map.entry("city","city"),Map.entry("country","country"),
                Map.entry("email","email"),Map.entry("phone","phone"),Map.entry("registerName","register_name"),
                Map.entry("registerCourt","register_court"),Map.entry("registerNumber","register_number"),
                Map.entry("vatId","vat_id"),Map.entry("businessId","business_id"),
                Map.entry("supervisoryAuthority","supervisory_authority"),
                Map.entry("editorialResponsibleName","editorial_responsible_name"),
                Map.entry("editorialResponsibleStreet","editorial_responsible_street"),
                Map.entry("editorialResponsiblePostalCode","editorial_responsible_postal_code"),
                Map.entry("editorialResponsibleCity","editorial_responsible_city"),
                Map.entry("editorialResponsibleCountry","editorial_responsible_country"),
                Map.entry("disputeResolutionText","dispute_resolution_text"),
                Map.entry("additionalInformation","additional_information"));
        columns.forEach((parameter,column) -> {
            if (!java.util.Objects.equals(previous.get(column), next.get(parameter))) changed.add(column);
        });
        return changed.isEmpty() ? List.of("source") : changed;
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static String s(Map<String,Object> row, String key) { return RowValues.string(row,key); }
    private static String value(String value) { return value == null ? "" : value.strip(); }
}
