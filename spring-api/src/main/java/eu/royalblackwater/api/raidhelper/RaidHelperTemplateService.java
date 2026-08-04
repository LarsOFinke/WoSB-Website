package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static eu.royalblackwater.api.raidhelper.RaidHelperProfileService.requireAdmin;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.RaidHelperTemplateRead;
import eu.royalblackwater.api.contract.RaidHelperTemplateWrite;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class RaidHelperTemplateService {
    private static final String BASE_QUERY = """
            select t.*, p.name profile_name
            from raid_helper_templates t join raid_helper_profiles p on p.id=t.profile_id
            """;

    private final JdbcQueryService jdbc;
    private final RaidHelperPolicy policy;
    private final AuditService audit;
    private final Clock clock;

    public RaidHelperTemplateService(JdbcQueryService jdbc, RaidHelperPolicy policy,
                                     AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }

    public List<RaidHelperTemplateRead> list(AuthenticatedUser actor) {
        requireAdmin(actor);
        return jdbc.query(BASE_QUERY + " order by lower(t.name), t.id", Map.of()).stream()
                .map(this::read).toList();
    }

    @Transactional
    public RaidHelperTemplateRead create(AuthenticatedUser actor, RaidHelperTemplateWrite payload) {
        requireAdmin(actor);
        ValidatedTemplate value = validate(payload);
        try {
            long id = jdbc.insertReturningId("""
                    insert into raid_helper_templates
                      (profile_id, name, raid_template_id, scope_type, title_template, description_template,
                       announcement_template, payload_template_json, uses_premium_features,
                       is_default, is_active, created_at, updated_at)
                    values (:profileId, :name, :raidTemplateId, :scopeType, :titleTemplate, :descriptionTemplate,
                            :announcementTemplate, :payloadTemplate, :premium, :isDefault, :isActive, :now, :now)
                    returning id
                    """, value.parameters(now()));
            replaceCategories(id, value.categories());
            audit.record(actor, "raid_helper_template", id, "create", "Raid-Helper template created.",
                    changedFields());
            return get(id);
        } catch (DataIntegrityViolationException exception) {
            throw duplicate(exception);
        }
    }

    @Transactional
    public RaidHelperTemplateRead update(AuthenticatedUser actor, long templateId, RaidHelperTemplateWrite payload) {
        requireAdmin(actor);
        Map<String, Object> current = row(templateId);
        ValidatedTemplate value = validate(payload);
        if (hasLinks(templateId) && longValue(current, "profile_id") != value.profileId()) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "A template used by synchronized events cannot move to another profile; create a new template instead.");
        }
        try {
            jdbc.update("""
                    update raid_helper_templates set profile_id=:profileId, name=:name,
                      raid_template_id=:raidTemplateId, scope_type=:scopeType, title_template=:titleTemplate,
                      description_template=:descriptionTemplate, announcement_template=:announcementTemplate,
                      payload_template_json=:payloadTemplate, uses_premium_features=:premium,
                      is_default=:isDefault, is_active=:isActive, updated_at=:now
                    where id=:id
                    """, merge(value.parameters(now()), "id", templateId));
            replaceCategories(templateId, value.categories());
            audit.record(actor, "raid_helper_template", templateId, "update", "Raid-Helper template updated.",
                    changedFields());
            return get(templateId);
        } catch (DataIntegrityViolationException exception) {
            throw duplicate(exception);
        }
    }

    @Transactional
    public void delete(AuthenticatedUser actor, long templateId) {
        requireAdmin(actor);
        row(templateId);
        if (hasLinks(templateId)) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "Templates used by synchronized events cannot be deleted; deactivate them instead.");
        }
        jdbc.update("delete from raid_helper_templates where id=:id", Map.of("id", templateId));
        audit.record(actor, "raid_helper_template", templateId, "delete", "Raid-Helper template deleted.", List.of());
    }

    public Map<String, Object> detail(long id) {
        return jdbc.optional(BASE_QUERY + " where t.id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper template not found."));
    }

    private RaidHelperTemplateRead get(long id) {
        return read(detail(id));
    }

    private Map<String, Object> row(long id) {
        return jdbc.optional("select * from raid_helper_templates where id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper template not found."));
    }

    private RaidHelperTemplateRead read(Map<String, Object> row) {
        long id = longValue(row, "id");
        List<String> categories = jdbc.query("""
                select category from raid_helper_template_categories where template_id=:id order by category
                """, Map.of("id", id)).stream().map(value -> requiredString(value, "category")).toList();
        return new RaidHelperTemplateRead(requiredString(row, "announcement_template"), categories,
                dateTime(row, "created_at"), requiredString(row, "description_template"), id,
                booleanValue(row, "is_active"), booleanValue(row, "is_default"), requiredString(row, "name"),
                requiredString(row, "payload_template_json"), longValue(row, "profile_id"),
                requiredString(row, "profile_name"), requiredString(row, "raid_template_id"),
                requiredString(row, "scope_type"), requiredString(row, "title_template"),
                dateTime(row, "updated_at"), booleanValue(row, "uses_premium_features"));
    }

    private ValidatedTemplate validate(RaidHelperTemplateWrite payload) {
        if (jdbc.count("select count(*) from raid_helper_profiles where id=:id", Map.of("id", payload.profileId())) == 0) {
            throw new ResponseStatusException(BAD_REQUEST, "Raid-Helper profile not found.");
        }
        String scope = payload.scopeType() == null || payload.scopeType().isBlank()
                ? "both" : payload.scopeType().strip().toLowerCase();
        if (!Set.of("both", "fleet", "squad").contains(scope)) {
            throw new ResponseStatusException(BAD_REQUEST, "Invalid template scope.");
        }
        boolean premium = policy.flag(payload.usesPremiumFeatures(), false);
        String raidTemplateId = payload.raidTemplateId() == null ? "" : payload.raidTemplateId().strip();
        return new ValidatedTemplate(payload.profileId(), policy.cleanName(payload.name(), "Template name"),
                raidTemplateId, scope, policy.categories(payload.categories()),
                blankDefault(payload.titleTemplate(), "{{event.title}}"),
                blankDefault(payload.descriptionTemplate(), "{{event.description}}"),
                payload.announcementTemplate() == null ? "" : payload.announcementTemplate().strip(),
                policy.payloadTemplate(payload.payloadTemplateJson(), raidTemplateId, premium), premium,
                policy.flag(payload.isDefault(), false), policy.flag(payload.isActive(), true));
    }

    private void replaceCategories(long id, List<String> categories) {
        jdbc.update("delete from raid_helper_template_categories where template_id=:id", Map.of("id", id));
        for (String category : categories) {
            jdbc.update("insert into raid_helper_template_categories (template_id, category) values (:id, :category)",
                    Map.of("id", id, "category", category));
        }
    }

    private boolean hasLinks(long id) {
        return jdbc.count("select count(*) from raid_helper_event_links where template_id=:id", Map.of("id", id)) > 0;
    }

    private static List<String> changedFields() {
        return List.of("profile_id", "raid_template_id", "scope_type", "categories", "title_template",
                "description_template", "announcement_template", "payload_template_json",
                "uses_premium_features", "is_default", "is_active");
    }

    private static String blankDefault(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.strip();
    }

    private static Map<String, Object> merge(Map<String, Object> source, String name, Object value) {
        java.util.LinkedHashMap<String, Object> result = new java.util.LinkedHashMap<>(source);
        result.put(name, value);
        return result;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static ResponseStatusException duplicate(DataIntegrityViolationException exception) {
        return new ResponseStatusException(BAD_REQUEST,
                "A template with this name already exists in the selected profile.", exception);
    }

    private record ValidatedTemplate(long profileId, String name, String raidTemplateId, String scopeType,
                                     List<String> categories, String titleTemplate, String descriptionTemplate,
                                     String announcementTemplate, String payloadTemplate, boolean premium,
                                     boolean isDefault, boolean isActive) {
        Map<String, Object> parameters(LocalDateTime now) {
            return SqlParameters.ofNullable("profileId", profileId, "name", name,
                    "raidTemplateId", raidTemplateId, "scopeType", scopeType,
                    "titleTemplate", titleTemplate, "descriptionTemplate", descriptionTemplate,
                    "announcementTemplate", announcementTemplate, "payloadTemplate", payloadTemplate,
                    "premium", premium, "isDefault", isDefault, "isActive", isActive, "now", now);
        }
    }
}
