package eu.royalblackwater.api.guides;

import eu.royalblackwater.api.account.UserReferenceService;
import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.builds.BuildService;
import eu.royalblackwater.api.content.ContentEmbedValidator;
import eu.royalblackwater.api.contract.BuildRead;
import eu.royalblackwater.api.contract.FileRead;
import eu.royalblackwater.api.contract.GuideCreate;
import eu.royalblackwater.api.contract.GuideRead;
import eu.royalblackwater.api.contract.GuideSummary;
import eu.royalblackwater.api.contract.GuideUpdate;
import eu.royalblackwater.api.contract.UserReferenceRead;
import eu.royalblackwater.api.files.FileAssetService;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
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
    private static final String SUMMARY = """
            select g.id,g.title,g.category,g.summary,g.owner_id,g.created_at,g.updated_at,
                   coalesce((select count(*) from guide_attachments a where a.guide_id=g.id),0) attachment_count,
                   coalesce((select count(*) from guide_build_references r where r.guide_id=g.id),0) build_reference_count
              from guides g
            """;
    private final JdbcQueryService jdbc;
    private final FileAssetService files;
    private final BuildService builds;
    private final UserReferenceService users;
    private final ContentEmbedValidator embeds;
    private final AuditService audit;
    private final Clock clock;

    public GuideService(JdbcQueryService jdbc, FileAssetService files, BuildService builds,
                        UserReferenceService users, ContentEmbedValidator embeds, AuditService audit, Clock clock) {
        this.jdbc = jdbc; this.files = files; this.builds = builds; this.users = users;
        this.embeds = embeds; this.audit = audit; this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<GuideSummary> list(String search, String category, int limit, int offset, AuthenticatedUser actor) {
        StringBuilder sql = new StringBuilder(SUMMARY + " where g.is_published=true");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (search != null && !search.isBlank()) {
            sql.append(" and (g.title ilike :search or coalesce(g.summary,'') ilike :search or g.body ilike :search)");
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (category != null && !category.isBlank()) {
            sql.append(" and g.category=:category"); parameters.put("category", normalizeCategory(category));
        }
        sql.append(" order by g.updated_at desc,g.id desc limit :limit offset :offset");
        parameters.put("limit", limit);
        parameters.put("offset", offset);
        return summaries(jdbc.query(sql.toString(), parameters));
    }

    @Transactional(readOnly = true)
    public List<GuideSummary> listForAdministration(int limit, int offset) {
        return summaries(jdbc.query(SUMMARY + " order by g.updated_at desc,g.id desc limit :limit offset :offset",
                Map.of("limit", limit, "offset", offset)));
    }

    @Transactional(readOnly = true)
    public GuideRead get(long guideId, AuthenticatedUser actor) {
        Map<String, Object> row = jdbc.optional(SUMMARY + " where g.id=:id and g.is_published=true", Map.of("id", guideId))
                .orElseThrow(GuideService::notFound);
        List<FileRead> attachments = files.attachments("guide_attachments", "guide_id", guideId);
        List<BuildRead> linkedBuilds = linkedBuilds(guideId, actor);
        GuideSummary summary = summary(row, users.readMany(List.of(RowValues.longValue(row, "owner_id"))));
        return new GuideRead(summary.attachmentCount(), attachments,
                jdbc.required("select body from guides where id=:id", Map.of("id", guideId)).get("body").toString(),
                summary.buildReferenceCount(), linkedBuilds, summary.category(), summary.createdAt(), summary.id(),
                summary.owner(), summary.ownerId(), summary.summary(), summary.title(), summary.updatedAt());
    }

    @Transactional
    public GuideRead create(GuideCreate payload, AuthenticatedUser actor) {
        Prepared prepared = prepare(payload.body(), payload.fileIds(), payload.buildIds(), actor);
        LocalDateTime now = now();
        long id = jdbc.insertReturningId("""
                insert into guides(title,category,summary,body,owner_id,is_published,created_at,updated_at)
                values(:title,:category,:summary,:body,:ownerId,true,:now,:now) returning id
                """, SqlParameters.ofNullable("title", payload.title().strip(), "category", normalizeCategory(payload.category()),
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
        jdbc.update("""
                update guides set title=:title,category=:category,summary=:summary,body=:body,updated_at=:now
                 where id=:id and is_published=true
                """, SqlParameters.ofNullable("title", payload.title().strip(), "category", normalizeCategory(payload.category()),
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
        if (jdbc.update("update guides set is_published=false,updated_at=:now where id=:id and is_published=true",
                Map.of("now", now(), "id", guideId)) == 0) throw notFound();
        files.refreshPublication(fileIds);
        audit.record(actor, "guide", guideId, "delete", "Guide unpublished.", List.of("is_published"));
    }

    private Prepared prepare(String body, List<Long> fileIds, List<Long> buildIds, AuthenticatedUser actor) {
        List<Map<String, Object>> selectedFiles = files.ownedFiles(fileIds, actor);
        List<Long> normalizedBuildIds = distinctPositive(buildIds);
        builds.getMany(normalizedBuildIds, actor);
        List<Long> normalizedFileIds = selectedFiles.stream().map(row -> RowValues.longValue(row, "id")).toList();
        embeds.validateFiles(body, normalizedFileIds); embeds.validateBuilds(body, normalizedBuildIds);
        return new Prepared(selectedFiles, normalizedFileIds, normalizedBuildIds);
    }

    private void replaceLinks(long guideId, Prepared prepared) {
        files.attach("guide_attachments", "guide_id", guideId, prepared.files(), "guide");
        jdbc.update("delete from guide_build_references where guide_id=:id", Map.of("id", guideId));
        int order = 0;
        for (Long buildId : prepared.buildIds()) {
            jdbc.update("""
                    insert into guide_build_references(guide_id,build_id,sort_order)
                    values(:guideId,:buildId,:sortOrder)
                    """, Map.of("guideId", guideId, "buildId", buildId, "sortOrder", order++));
        }
    }

    private List<BuildRead> linkedBuilds(long guideId, AuthenticatedUser actor) {
        List<Long> ids = jdbc.query("""
                select build_id from guide_build_references where guide_id=:id order by sort_order,id
                """, Map.of("id", guideId)).stream()
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
        return new GuideSummary(RowValues.longValue(row, "attachment_count"), RowValues.longValue(row, "build_reference_count"),
                RowValues.requiredString(row, "category"), RowValues.dateTime(row, "created_at"), RowValues.longValue(row, "id"),
                owner, ownerId, RowValues.string(row, "summary"), RowValues.requiredString(row, "title"),
                RowValues.dateTime(row, "updated_at"));
    }

    private Map<String, Object> raw(long id) {
        return jdbc.optional("select * from guides where id=:id and is_published=true", Map.of("id", id))
                .orElseThrow(GuideService::notFound);
    }

    private Set<Long> attachmentIds(long guideId) {
        Set<Long> result = new LinkedHashSet<>();
        for (Map<String, Object> row : jdbc.query("select file_id from guide_attachments where guide_id=:id", Map.of("id", guideId))) {
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
    private record Prepared(List<Map<String, Object>> files, List<Long> fileIds, List<Long> buildIds) { }
}
