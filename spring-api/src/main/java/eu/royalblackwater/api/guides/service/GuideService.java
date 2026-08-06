package eu.royalblackwater.api.guides.service;

import eu.royalblackwater.api.account.service.UserReferenceService;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.service.BuildService;
import eu.royalblackwater.api.content.service.ContentEmbedValidator;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.FileRead;
import eu.royalblackwater.api.dto.GuideCreate;
import eu.royalblackwater.api.dto.GuideRead;
import eu.royalblackwater.api.dto.GuideSummary;
import eu.royalblackwater.api.dto.GuideUpdate;
import eu.royalblackwater.api.dto.UserReferenceRead;
import eu.royalblackwater.api.files.dto.StoredFileDto;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.guides.mapper.GuideDtoMapper;
import eu.royalblackwater.api.guides.repository.GuideRepository;
import eu.royalblackwater.api.guides.repository.queries.GuideQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class GuideService {
    private static final Set<String> CATEGORIES = Set.of(
            "general", "combat", "boarding", "gunnery", "sailing", "trading", "events", "fleet", "newcomer");
    private final GuideRepository repository;
    private final FileAssetService files;
    private final BuildService builds;
    private final UserReferenceService users;
    private final ContentEmbedValidator embeds;
    private final AuditService audit;
    private final Clock clock;

    public GuideService(GuideRepository repository, FileAssetService files, BuildService builds,
                        UserReferenceService users, ContentEmbedValidator embeds, AuditService audit, Clock clock) {
        this.repository = repository; this.files = files; this.builds = builds; this.users = users;
        this.embeds = embeds; this.audit = audit; this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<GuideSummary> list(String search, String category, int limit, int offset, AuthenticatedUser actor) {
        StringBuilder sql = new StringBuilder(GuideQueries.SUMMARY + GuideQueries.LIST_WHERE_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (search != null && !search.isBlank()) {
            sql.append(GuideQueries.LIST_AND_01);
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (category != null && !category.isBlank()) {
            sql.append(GuideQueries.LIST_AND_02); parameters.put("category", normalizeCategory(category));
        }
        sql.append(GuideQueries.LIST_ORDER_BY_01);
        parameters.put("limit", limit);
        parameters.put("offset", offset);
        return summaries(repository.query(sql.toString(), parameters));
    }

    @Transactional(readOnly = true)
    public List<GuideSummary> listForAdministration(int limit, int offset) {
        return summaries(repository.query(GuideQueries.SUMMARY + GuideQueries.LIST_ORDER_BY_01,
                Map.of("limit", limit, "offset", offset)));
    }

    @Transactional(readOnly = true)
    public GuideRead get(long guideId, AuthenticatedUser actor) {
        Map<String, Object> row = repository.optional(GuideQueries.SUMMARY + GuideQueries.GET_WHERE_01, Map.of("id", guideId))
                .orElseThrow(GuideService::notFound);
        List<FileRead> attachments = files.attachments("guide_attachments", "guide_id", guideId);
        List<BuildRead> linkedBuilds = linkedBuilds(guideId, actor);
        GuideSummary summary = summary(row, users.readMany(List.of(RowValues.longValue(row, "owner_id"))));
        return GuideDtoMapper.detail(summary, attachments,
                repository.required(GuideQueries.GET_SELECT_01, Map.of("id", guideId)).get("body").toString(),
                linkedBuilds);
    }

    @Transactional
    public GuideRead create(GuideCreate payload, AuthenticatedUser actor) {
        Prepared prepared = prepare(payload.body(), payload.fileIds(), payload.buildIds(), actor);
        LocalDateTime now = now();
        long id = repository.insertReturningId(GuideQueries.CREATE_INSERT_01, SqlParameters.ofNullable("title", payload.title().strip(), "category", normalizeCategory(payload.category()),
                "summary", normalize(payload.summary()), "body", payload.body(), "ownerId", actor.id(), "now", now));
        replaceLinks(id, prepared);
        audit.record(actor, "guide", id, "create", "Guide created.", List.of("title", "category", "body", "file_ids", "build_ids"));
        return get(id, actor);
    }

    @Transactional
    public GuideRead update(long guideId, GuideUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> guide = raw(guideId);
        requireOwnerOrStaff(RowValues.longValue(guide, "owner_id"), actor);
        Prepared prepared = prepare(payload.body(), payload.fileIds(), payload.buildIds(), actor);
        Set<Long> previousFiles = attachmentIds(guideId);
        repository.update(GuideQueries.UPDATE_UPDATE_01, SqlParameters.ofNullable("title", payload.title().strip(), "category", normalizeCategory(payload.category()),
                "summary", normalize(payload.summary()), "body", payload.body(), "now", now(), "id", guideId));
        replaceLinks(guideId, prepared);
        Set<Long> refresh = new LinkedHashSet<>(previousFiles); refresh.addAll(prepared.fileIds());
        files.refreshPublication(refresh);
        audit.record(actor, "guide", guideId, "update", "Guide updated.", List.of("title", "category", "body", "file_ids", "build_ids"));
        return get(guideId, actor);
    }

    @Transactional
    public void delete(long guideId, AuthenticatedUser actor, boolean administrator) {
        Map<String, Object> guide = raw(guideId);
        if (!administrator) requireOwnerOrStaff(RowValues.longValue(guide, "owner_id"), actor);
        Set<Long> fileIds = attachmentIds(guideId);
        if (repository.update(GuideQueries.DELETE_UPDATE_01,
                Map.of("now", now(), "id", guideId)) == 0) throw notFound();
        files.refreshPublication(fileIds);
        audit.record(actor, "guide", guideId, "delete", "Guide unpublished.", List.of("is_published"));
    }

    private Prepared prepare(String body, List<Long> fileIds, List<Long> buildIds, AuthenticatedUser actor) {
        List<StoredFileDto> selectedFiles = files.ownedFiles(fileIds, actor);
        List<Long> normalizedBuildIds = distinctPositive(buildIds);
        builds.getMany(normalizedBuildIds, actor);
        List<Long> normalizedFileIds = selectedFiles.stream().map(StoredFileDto::id).toList();
        embeds.validateFiles(body, normalizedFileIds); embeds.validateBuilds(body, normalizedBuildIds);
        return new Prepared(selectedFiles, normalizedFileIds, normalizedBuildIds);
    }

    private void replaceLinks(long guideId, Prepared prepared) {
        files.attach("guide_attachments", "guide_id", guideId, prepared.files(), "guide");
        repository.update(GuideQueries.REPLACE_LINKS_DELETE_01, Map.of("id", guideId));
        int order = 0;
        for (Long buildId : prepared.buildIds()) {
            repository.update(GuideQueries.REPLACE_LINKS_INSERT_01, Map.of("guideId", guideId, "buildId", buildId, "sortOrder", order++));
        }
    }

    private List<BuildRead> linkedBuilds(long guideId, AuthenticatedUser actor) {
        List<Long> ids = repository.query(GuideQueries.LINKED_BUILDS_SELECT_01, Map.of("id", guideId)).stream()
                .map(row -> RowValues.longValue(row, "build_id"))
                .toList();
        return builds.getMany(ids, actor);
    }

    private List<GuideSummary> summaries(List<Map<String, Object>> rows) {
        Map<Long, UserReferenceRead> owners = users.readMany(rows.stream()
                .map(row -> RowValues.longValue(row, "owner_id"))
                .toList());
        return rows.stream().map(row -> summary(row, owners)).toList();
    }

    private GuideSummary summary(Map<String, Object> row, Map<Long, UserReferenceRead> owners) {
        long ownerId = RowValues.longValue(row, "owner_id");
        UserReferenceRead owner = owners.get(ownerId);
        if (owner == null) throw new IllegalStateException("Guide owner is missing: " + ownerId);
        return GuideDtoMapper.summary(row, owner);
    }

    private Map<String, Object> raw(long id) {
        return repository.optional(GuideQueries.RAW_SELECT_01, Map.of("id", id))
                .orElseThrow(GuideService::notFound);
    }

    private Set<Long> attachmentIds(long guideId) {
        Set<Long> result = new LinkedHashSet<>();
        for (Map<String, Object> row : repository.query(GuideQueries.ATTACHMENT_IDS_SELECT_01, Map.of("id", guideId))) {
            result.add(RowValues.longValue(row, "file_id"));
        }
        return result;
    }

    private static List<Long> distinctPositive(List<Long> values) {
        LinkedHashSet<Long> result = new LinkedHashSet<>();
        if (values != null) for (Long value : values) if (value != null && value > 0) result.add(value);
        return List.copyOf(result);
    }
    private static String normalizeCategory(String value) {
        String category = value == null ? "general" : value.strip().toLowerCase(Locale.ROOT).replace(' ', '_').replace('-', '_');
        return CATEGORIES.contains(category) ? category : "general";
    }
    private static String normalize(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private static void requireOwnerOrStaff(long ownerId, AuthenticatedUser actor) { if (ownerId != actor.id() && !actor.staff()) throw notFound(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Guide not found."); }
    private record Prepared(List<StoredFileDto> files, List<Long> fileIds, List<Long> buildIds) { }
}
