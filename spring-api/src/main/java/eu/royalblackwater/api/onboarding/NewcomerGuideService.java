package eu.royalblackwater.api.onboarding;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.NewcomerGuideBlockInput;
import eu.royalblackwater.api.contract.NewcomerGuideBlockRead;
import eu.royalblackwater.api.contract.NewcomerGuideRead;
import eu.royalblackwater.api.contract.NewcomerGuideResourceInput;
import eu.royalblackwater.api.contract.NewcomerGuideResourceRead;
import eu.royalblackwater.api.contract.NewcomerGuideUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.net.URI;
import java.net.URISyntaxException;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;

@Service
public class NewcomerGuideService {
    private static final long PAGE_ID = 1;
    private static final Set<String> BLOCK_TYPES = Set.of("text", "resources");
    private static final Set<String> RESOURCE_TYPES = Set.of("guide", "build", "internal", "external");
    private final JdbcQueryService jdbc;
    private final AuditService audit;
    private final Clock clock;

    public NewcomerGuideService(JdbcQueryService jdbc, AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional
    public NewcomerGuideRead get() {
        ensurePage();
        return read();
    }

    @Transactional
    public NewcomerGuideRead replace(NewcomerGuideUpdate payload, AuthenticatedUser actor) {
        if (!actor.staff()) throw new ResponseStatusException(FORBIDDEN, "Staff access required.");
        ensurePage();
        String title = required(payload.title(), "Guide title is required.");
        String intro = payload.intro() == null ? "" : payload.intro().strip();
        List<NewcomerGuideBlockInput> blocks = payload.blocks() == null ? List.of() : payload.blocks();
        validate(blocks);
        LocalDateTime now = now();
        jdbc.update("""
                update newcomer_guide_pages set title=:title,intro=:intro,updated_by_id=:userId,updated_at=:now where id=:id
                """, Map.of("title", title, "intro", intro, "userId", actor.id(), "now", now, "id", PAGE_ID));
        jdbc.update("delete from newcomer_guide_blocks where page_id=:id", Map.of("id", PAGE_ID));
        int blockOrder = 10;
        for (NewcomerGuideBlockInput block : blocks) {
            long blockId = jdbc.insertReturningId("""
                    insert into newcomer_guide_blocks(page_id,block_type,title,body,sort_order)
                    values(:pageId,:type,:title,:body,:sortOrder) returning id
                    """, SqlParameters.ofNullable("pageId", PAGE_ID, "type", block.blockType(),
                            "title", block.title().strip(), "body", blank(block.body()), "sortOrder", blockOrder));
            int resourceOrder = 10;
            for (NewcomerGuideResourceInput resource : resources(block)) {
                jdbc.insertReturningId("""
                        insert into newcomer_guide_resources(block_id,resource_type,resource_id,label,description,url,sort_order)
                        values(:blockId,:type,:resourceId,:label,:description,:url,:sortOrder) returning id
                        """, SqlParameters.ofNullable(
                                "blockId", blockId, "type", resource.resourceType(), "resourceId", resource.resourceId(),
                                "label", blank(resource.label()), "description", blank(resource.description()),
                                "url", blank(resource.url()), "sortOrder", resourceOrder));
                resourceOrder += 10;
            }
            blockOrder += 10;
        }
        audit.record(actor, "newcomer_guide", PAGE_ID, "update", "Starter guide updated.",
                List.of("title", "intro", "blocks"));
        return read();
    }

    private NewcomerGuideRead read() {
        Map<String, Object> page = jdbc.required("""
                select p.*,coalesce(nullif(up.display_name,''),u.username) updated_by
                from newcomer_guide_pages p left join users u on u.id=p.updated_by_id
                left join user_profiles up on up.user_id=u.id where p.id=:id
                """, Map.of("id", PAGE_ID));
        List<Map<String, Object>> blockRows = jdbc.query("""
                select * from newcomer_guide_blocks where page_id=:id order by sort_order,id
                """, Map.of("id", PAGE_ID));
        Map<Long, List<NewcomerGuideResourceRead>> resourcesByBlock = new LinkedHashMap<>();
        if (!blockRows.isEmpty()) {
            List<Long> blockIds = blockRows.stream().map(row -> RowValues.longValue(row, "id")).toList();
            for (Map<String, Object> resource : jdbc.query("""
                    select r.*,g.title guide_title,g.summary guide_summary,g.is_published,
                           b.build_name
                    from newcomer_guide_resources r
                    left join guides g on r.resource_type='guide' and g.id=r.resource_id
                    left join builds b on r.resource_type='build' and b.id=r.resource_id
                    where r.block_id in (:ids) order by r.block_id,r.sort_order,r.id
                    """, Map.of("ids", blockIds))) {
                resourcesByBlock.computeIfAbsent(RowValues.longValue(resource, "block_id"), ignored -> new ArrayList<>())
                        .add(resourceRead(resource));
            }
        }
        List<NewcomerGuideBlockRead> blocks = blockRows.stream().map(block -> {
            long blockId = RowValues.longValue(block, "id");
            return new NewcomerGuideBlockRead(RowValues.requiredString(block, "block_type"),
                    RowValues.string(block, "body"), blockId,
                    List.copyOf(resourcesByBlock.getOrDefault(blockId, List.of())),
                    RowValues.requiredString(block, "title"));
        }).toList();
        return new NewcomerGuideRead(List.copyOf(blocks), PAGE_ID, RowValues.requiredString(page, "intro"),
                RowValues.requiredString(page, "title"), RowValues.dateTime(page, "updated_at"),
                RowValues.string(page, "updated_by"));
    }

    private NewcomerGuideResourceRead resourceRead(Map<String, Object> row) {
        String type = RowValues.requiredString(row, "resource_type");
        Long resourceId = RowValues.nullableLong(row, "resource_id");
        String label = RowValues.string(row, "label");
        String description = RowValues.string(row, "description");
        String href;
        boolean available = true;
        if ("guide".equals(type)) {
            available = row.get("is_published") instanceof Boolean published && published;
            if (label == null) label = RowValues.string(row, "guide_title");
            if (description == null) description = RowValues.string(row, "guide_summary");
            href = resourceId == null ? "#" : "/guides/" + resourceId;
        } else if ("build".equals(type)) {
            available = RowValues.string(row, "build_name") != null;
            if (label == null) label = RowValues.string(row, "build_name");
            href = resourceId == null ? "#" : "/builds/" + resourceId;
        } else {
            href = validatedHref(type, RowValues.string(row, "url"));
            if (label == null) label = href;
        }
        if (label == null || label.isBlank()) label = "Unavailable resource";
        return new NewcomerGuideResourceRead(available, description, href, RowValues.longValue(row, "id"),
                label, resourceId, type);
    }

    private void validate(List<NewcomerGuideBlockInput> blocks) {
        Set<Long> guideIds = new LinkedHashSet<>();
        Set<Long> buildIds = new LinkedHashSet<>();
        for (NewcomerGuideBlockInput block : blocks) {
            if (!BLOCK_TYPES.contains(block.blockType())) throw bad("Unsupported guide block type.");
            required(block.title(), "Block title is required.");
            if ("text".equals(block.blockType()) && blank(block.body()) == null) {
                throw bad("Text blocks require body content.");
            }
            for (NewcomerGuideResourceInput resource : resources(block)) {
                String type = resource.resourceType();
                if (!RESOURCE_TYPES.contains(type)) throw bad("Unsupported guide resource type.");
                if ("guide".equals(type)) {
                    if (resource.resourceId() == null) throw bad("The selected guide does not exist or is not published.");
                    guideIds.add(resource.resourceId());
                } else if ("build".equals(type)) {
                    if (resource.resourceId() == null) throw bad("The selected build does not exist.");
                    buildIds.add(resource.resourceId());
                } else {
                    validatedHref(type, resource.url());
                }
            }
        }
        requireReferences(guideIds,
                "select id from guides where id in (:ids) and is_published=true",
                "The selected guide does not exist or is not published.");
        requireReferences(buildIds, "select id from builds where id in (:ids)",
                "The selected build does not exist.");
    }

    private void requireReferences(Set<Long> expected, String sql, String message) {
        if (expected.isEmpty()) return;
        Set<Long> found = new LinkedHashSet<>();
        for (Map<String, Object> row : jdbc.query(sql, Map.of("ids", List.copyOf(expected)))) {
            found.add(RowValues.longValue(row, "id"));
        }
        if (!found.equals(expected)) throw bad(message);
    }

    private void ensurePage() {
        if (jdbc.count("select count(*) from newcomer_guide_pages where id=:id", Map.of("id", PAGE_ID)) > 0) return;
        LocalDateTime now = now();
        jdbc.update("""
                insert into newcomer_guide_pages(id,title,intro,created_at,updated_at)
                values(:id,:title,:intro,:now,:now) on conflict(id) do nothing
                """, Map.of("id", PAGE_ID, "title", "New Captain Guide",
                        "intro", "A curated route from first login to prepared fleet participation.", "now", now));
    }

    private static String validatedHref(String type, String value) {
        String url = value == null ? "" : value.strip();
        if ("internal".equals(type)) {
            if (!url.startsWith("/") || url.startsWith("//")) throw bad("Internal links must start with a single '/'.");
            return url;
        }
        try {
            URI uri = new URI(url);
            if (!("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme()))
                    || uri.getHost() == null) throw bad("External links must use a complete http(s) URL.");
            return uri.toASCIIString();
        } catch (URISyntaxException exception) {
            throw bad("External links must use a complete http(s) URL.");
        }
    }
    private static List<NewcomerGuideResourceInput> resources(NewcomerGuideBlockInput block) {
        return block.resources() == null || "text".equals(block.blockType()) ? List.of() : block.resources();
    }
    private static String required(String value, String message) { if (value == null || value.isBlank()) throw bad(message); return value.strip(); }
    private static String blank(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
