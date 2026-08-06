package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.RaidHelperTemplateRead;
import eu.royalblackwater.api.dto.RaidHelperTemplateWrite;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.dto.RaidHelperTemplateConfigDto;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperTemplateQueries;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
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

import static eu.royalblackwater.api.persistence.RowValues.*;
import static eu.royalblackwater.api.raidhelper.service.RaidHelperProfileService.requireAdmin;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class RaidHelperTemplateService {

    private final RaidHelperRepository repository;
    private final RaidHelperPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    private final RaidHelperDtoMapper mapper;

    public RaidHelperTemplateService(RaidHelperRepository repository, RaidHelperPolicy policy,
                                     AuditService audit, Clock clock, RaidHelperDtoMapper mapper) {
        this.repository = repository;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
        this.mapper = mapper;
    }

    public List<RaidHelperTemplateRead> list(AuthenticatedUser actor) {
        requireAdmin(actor);
        return repository.query(RaidHelperTemplateQueries.BASE_QUERY + RaidHelperTemplateQueries.LIST_ORDER_BY_01, Map.of()).stream()
                .map(this::toRead).toList();
    }

    @Transactional
    public RaidHelperTemplateRead create(AuthenticatedUser actor, RaidHelperTemplateWrite payload) {
        requireAdmin(actor);
        ValidatedTemplate value = validate(payload);
        try {
            long id = repository.insertReturningId(RaidHelperTemplateQueries.CREATE_INSERT_01, value.parameters(now()));
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
            repository.update(RaidHelperTemplateQueries.UPDATE_UPDATE_01, merge(value.parameters(now()), "id", templateId));
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
        repository.update(RaidHelperTemplateQueries.DELETE_DELETE_01, Map.of("id", templateId));
        audit.record(actor, "raid_helper_template", templateId, "delete", "Raid-Helper template deleted.", List.of());
    }

    public RaidHelperTemplateConfigDto configuration(long id, String timezone) {
        return mapper.templateConfig(detailRow(id), timezone);
    }

    private RaidHelperTemplateRead get(long id) {
        return toRead(detailRow(id));
    }

    private Map<String, Object> detailRow(long id) {
        return repository.optional(RaidHelperTemplateQueries.BASE_QUERY + RaidHelperTemplateQueries.DETAIL_WHERE_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper template not found."));
    }

    private Map<String, Object> row(long id) {
        return repository.optional(RaidHelperTemplateQueries.ROW_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper template not found."));
    }

    private RaidHelperTemplateRead toRead(Map<String, Object> row) {
        long id = longValue(row, "id");
        List<String> categories = repository.query(RaidHelperTemplateQueries.READ_SELECT_01, Map.of("id", id)).stream().map(value -> requiredString(value, "category")).toList();
        return mapper.templateRead(row, categories);
    }

    private ValidatedTemplate validate(RaidHelperTemplateWrite payload) {
        if (repository.count(RaidHelperTemplateQueries.VALIDATE_SELECT_01, Map.of("id", payload.profileId())) == 0) {
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
        repository.update(RaidHelperTemplateQueries.REPLACE_CATEGORIES_DELETE_01, Map.of("id", id));
        for (String category : categories) {
            repository.update(RaidHelperTemplateQueries.REPLACE_CATEGORIES_INSERT_01,
                    Map.of("id", id, "category", category));
        }
    }

    private boolean hasLinks(long id) {
        return repository.count(RaidHelperTemplateQueries.HAS_LINKS_SELECT_01, Map.of("id", id)) > 0;
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
