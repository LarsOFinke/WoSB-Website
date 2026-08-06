package eu.royalblackwater.api.onboarding.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.NewcomerGuideBlockInput;
import eu.royalblackwater.api.dto.NewcomerGuideBlockRead;
import eu.royalblackwater.api.dto.NewcomerGuideRead;
import eu.royalblackwater.api.dto.NewcomerGuideResourceInput;
import eu.royalblackwater.api.dto.NewcomerGuideResourceRead;
import eu.royalblackwater.api.dto.NewcomerGuideUpdate;
import eu.royalblackwater.api.onboarding.mapper.NewcomerGuideDtoMapper;
import eu.royalblackwater.api.onboarding.repository.NewcomerGuideRepository;
import eu.royalblackwater.api.onboarding.repository.queries.NewcomerGuideQueries;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
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
    private final NewcomerGuideRepository repository;
    private final AuditService audit;
    private final Clock clock;

    public NewcomerGuideService(NewcomerGuideRepository repository, AuditService audit, Clock clock) {
        this.repository = repository;
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
        repository.update(NewcomerGuideQueries.REPLACE_UPDATE_01, Map.of("title", title, "intro", intro, "userId", actor.id(), "now", now, "id", PAGE_ID));
        repository.update(NewcomerGuideQueries.REPLACE_DELETE_01, Map.of("id", PAGE_ID));
        int blockOrder = 10;
        for (NewcomerGuideBlockInput block : blocks) {
            long blockId = repository.insertReturningId(NewcomerGuideQueries.REPLACE_INSERT_01, SqlParameters.ofNullable("pageId", PAGE_ID, "type", block.blockType(),
                            "title", block.title().strip(), "body", blank(block.body()), "sortOrder", blockOrder));
            int resourceOrder = 10;
            for (NewcomerGuideResourceInput resource : resources(block)) {
                repository.insertReturningId(NewcomerGuideQueries.REPLACE_INSERT_02, SqlParameters.ofNullable(
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
        Map<String, Object> page = repository.required(NewcomerGuideQueries.READ_SELECT_01, Map.of("id", PAGE_ID));
        List<Map<String, Object>> blockRows = repository.query(NewcomerGuideQueries.READ_SELECT_02, Map.of("id", PAGE_ID));
        Map<Long, List<NewcomerGuideResourceRead>> resourcesByBlock = new LinkedHashMap<>();
        if (!blockRows.isEmpty()) {
            List<Long> blockIds = blockRows.stream().map(row -> RowValues.longValue(row, "id")).toList();
            for (Map<String, Object> resource : repository.query(NewcomerGuideQueries.READ_SELECT_03, Map.of("ids", blockIds))) {
                resourcesByBlock.computeIfAbsent(RowValues.longValue(resource, "block_id"), ignored -> new ArrayList<>())
                        .add(resourceRead(resource));
            }
        }
        List<NewcomerGuideBlockRead> blocks = blockRows.stream().map(block -> {
            long blockId = RowValues.longValue(block, "id");
            return NewcomerGuideDtoMapper.block(block, resourcesByBlock.getOrDefault(blockId, List.of()));
        }).toList();
        return NewcomerGuideDtoMapper.guide(page, PAGE_ID, blocks);
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
        return NewcomerGuideDtoMapper.resource(row, available, description, href, label, resourceId, type);
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
                NewcomerGuideQueries.VALIDATE_SELECT_01,
                "The selected guide does not exist or is not published.");
        requireReferences(buildIds, NewcomerGuideQueries.VALIDATE_SELECT_02,
                "The selected build does not exist.");
    }

    private void requireReferences(Set<Long> expected, String sql, String message) {
        if (expected.isEmpty()) return;
        Set<Long> found = new LinkedHashSet<>();
        for (Map<String, Object> row : repository.query(sql, Map.of("ids", List.copyOf(expected)))) {
            found.add(RowValues.longValue(row, "id"));
        }
        if (!found.equals(expected)) throw bad(message);
    }

    private void ensurePage() {
        if (repository.count(NewcomerGuideQueries.ENSURE_PAGE_SELECT_01, Map.of("id", PAGE_ID)) > 0) return;
        LocalDateTime now = now();
        repository.update(NewcomerGuideQueries.ENSURE_PAGE_INSERT_01, Map.of("id", PAGE_ID, "title", "New Captain Guide",
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
