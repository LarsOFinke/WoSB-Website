package eu.royalblackwater.api.legal.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.config.LegalNoticeProperties;
import eu.royalblackwater.api.dto.LegalNoticeAdminRead;
import eu.royalblackwater.api.dto.LegalNoticePublicRead;
import eu.royalblackwater.api.dto.LegalNoticeUpdate;
import eu.royalblackwater.api.legal.mapper.LegalNoticeDtoMapper;
import eu.royalblackwater.api.legal.repository.LegalNoticeRepository;
import eu.royalblackwater.api.legal.repository.queries.LegalNoticeQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LegalNoticeService {
    private static final int ID = 1;
    private final LegalNoticeRepository repository;
    private final LegalNoticeProperties environment;
    private final AuditService audit;
    private final Clock clock;

    public LegalNoticeService(LegalNoticeRepository repository, LegalNoticeProperties environment,
                              AuditService audit, Clock clock) {
        this.repository = repository;
        this.environment = environment;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public LegalNoticePublicRead publicNotice() {
        Map<String, Object> row = row().orElse(null);
        if (row == null || !RowValues.booleanValue(row, "published")) {
            return LegalNoticeDtoMapper.unpublished(row == null ? null : RowValues.dateTime(row, "updated_at"));
        }
        return LegalNoticeDtoMapper.published(row);
    }

    @Transactional
    public LegalNoticeAdminRead adminNotice() {
        ensureEnvironmentRow();
        return LegalNoticeDtoMapper.admin(requiredRow());
    }

    @Transactional
    public LegalNoticeAdminRead update(LegalNoticeUpdate payload, AuthenticatedUser actor) {
        ensureEnvironmentRow();
        Map<String, Object> previous = requiredRow();
        Map<String, Object> values = payloadValues(payload, true, actor.username());
        repository.update(updateSql(), values);
        audit.record(actor, "legal_notice", ID, "update", "Impressum settings updated.",
                changedFields(previous, values));
        return LegalNoticeDtoMapper.admin(requiredRow());
    }

    @Transactional
    public LegalNoticeAdminRead reset(AuthenticatedUser actor) {
        ensureEnvironmentRow();
        Map<String, Object> previous = requiredRow();
        Map<String, Object> values = environmentValues(false, "environment");
        repository.update(updateSql(), values);
        audit.record(actor, "legal_notice", ID, "restore",
                "Impressum settings restored from environment configuration.",
                changedFields(previous, values));
        return LegalNoticeDtoMapper.admin(requiredRow());
    }

    private void ensureEnvironmentRow() {
        Map<String, Object> values = environmentValues(false, "environment");
        repository.update(LegalNoticeQueries.ENSURE_ENVIRONMENT_ROW_INSERT_01, values);
    }

    private java.util.Optional<Map<String, Object>> row() {
        return repository.optional(LegalNoticeQueries.ROW_SELECT_01, Map.of("id", ID));
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
                "additionalInformation", value(p.additionalInformation()),
                "publicRepositoryUrl", value(p.publicRepositoryUrl()), "updatedBy", updatedBy,
                "updatedAt", UtcDateTimes.now(clock));
    }

    private Map<String, Object> environmentValues(boolean customized, String updatedBy) {
        return payloadValues(LegalNoticeDtoMapper.environmentUpdate(environment), customized, updatedBy);
    }

    private String updateSql() {
        return LegalNoticeQueries.UPDATE_SQL_UPDATE_01;
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
                Map.entry("additionalInformation","additional_information"),
                Map.entry("publicRepositoryUrl","public_repository_url"));
        columns.forEach((parameter,column) -> {
            if (!java.util.Objects.equals(previous.get(column), next.get(parameter))) changed.add(column);
        });
        return changed.isEmpty() ? List.of("source") : changed;
    }
    private static String value(String value) { return value == null ? "" : value.strip(); }
}
