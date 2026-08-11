package eu.royalblackwater.api.strategies.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.StrategyCreate;
import eu.royalblackwater.api.dto.StrategyRead;
import eu.royalblackwater.api.dto.StrategySummary;
import eu.royalblackwater.api.dto.StrategyUpdate;
import eu.royalblackwater.api.files.service.FileAssetService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.strategies.dto.PreparedStrategyOverlay;
import eu.royalblackwater.api.strategies.dto.StrategyBuildReference;
import eu.royalblackwater.api.strategies.mapper.StrategyMapper;
import eu.royalblackwater.api.strategies.repository.StrategyRepository;
import eu.royalblackwater.api.strategies.repository.queries.StrategyQueries;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class StrategyService {
    private final StrategyRepository repository;
    private final StrategyOverlayValidator overlays;
    private final FileAssetService files;
    private final AuditService audit;
    private final Clock clock;

    public StrategyService(StrategyRepository repository, StrategyOverlayValidator overlays,
                           FileAssetService files, AuditService audit, Clock clock) {
        this.repository = repository; this.overlays = overlays; this.files = files;
        this.audit = audit; this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<StrategySummary> mine(AuthenticatedUser actor) {
        return repository.query(StrategyQueries.MINE, Map.of("ownerId", actor.id())).stream()
                .map(StrategyMapper::summary).toList();
    }

    @Transactional(readOnly = true)
    public StrategyRead get(long id, AuthenticatedUser actor) {
        return StrategyMapper.read(owned(id, actor));
    }

    @Transactional(readOnly = true)
    public StrategyRead shared(String publicId) {
        UUID parsed;
        try { parsed = UUID.fromString(publicId); }
        catch (IllegalArgumentException exception) { throw notFound(); }
        return repository.optional(StrategyQueries.SHARED, Map.of("publicId", parsed))
                .map(StrategyMapper::read).orElseThrow(StrategyService::notFound);
    }

    @Transactional
    public StrategyRead create(StrategyCreate payload, AuthenticatedUser actor) {
        files.ownedImage(payload.backgroundFileId(), actor);
        PreparedStrategyOverlay overlay = prepare(payload.overlayJson());
        LocalDateTime now = now();
        long id = repository.insertReturningId(StrategyQueries.CREATE, SqlParameters.ofNullable(
                "ownerId", actor.id(), "backgroundFileId", payload.backgroundFileId(), "title", title(payload.title()),
                "description", optional(payload.description()), "overlayJson", overlay.json(),
                "publicId", UUID.randomUUID(), "now", now));
        replaceReferences(id, overlay);
        files.refreshPublication(Set.of(payload.backgroundFileId()));
        audit.record(actor, "strategy", id, "create", "Strategy created.",
                List.of("title", "background_file_id", "overlay_json"));
        return get(id, actor);
    }

    @Transactional
    public StrategyRead update(long id, StrategyUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> current = owned(id, actor);
        long previousFileId = RowValues.longValue(current, "id");
        files.ownedImage(payload.backgroundFileId(), actor);
        PreparedStrategyOverlay overlay = prepare(payload.overlayJson());
        int changed = repository.update(StrategyQueries.UPDATE, SqlParameters.ofNullable(
                "id", id, "ownerId", actor.id(), "backgroundFileId", payload.backgroundFileId(),
                "title", title(payload.title()), "description", optional(payload.description()),
                "overlayJson", overlay.json(), "now", now()));
        if (changed == 0) throw notFound();
        replaceReferences(id, overlay);
        files.refreshPublication(fileIds(previousFileId, payload.backgroundFileId()));
        audit.record(actor, "strategy", id, "update", "Strategy updated.",
                List.of("title", "description", "background_file_id", "overlay_json"));
        return get(id, actor);
    }

    @Transactional
    public StrategyRead publication(long id, boolean published, AuthenticatedUser actor) {
        Map<String, Object> current = owned(id, actor);
        LocalDateTime now = now();
        repository.update(StrategyQueries.PUBLISH, SqlParameters.ofNullable("id", id, "ownerId", actor.id(),
                "published", published, "publishedAt", published ? now : null, "now", now));
        files.refreshPublication(Set.of(RowValues.longValue(current, "id")));
        audit.record(actor, "strategy", id, published ? "publish" : "unpublish",
                published ? "Strategy published." : "Strategy unpublished.", List.of("is_published"));
        return get(id, actor);
    }

    @Transactional
    public void delete(long id, AuthenticatedUser actor) {
        Map<String, Object> current = owned(id, actor);
        long fileId = RowValues.longValue(current, "id");
        if (repository.update(StrategyQueries.DELETE, Map.of("id", id, "ownerId", actor.id())) == 0) throw notFound();
        files.refreshPublication(Set.of(fileId));
        audit.record(actor, "strategy", id, "delete", "Strategy deleted.", List.of());
    }

    private PreparedStrategyOverlay prepare(String value) {
        PreparedStrategyOverlay overlay = overlays.prepare(value);
        requireReferences(StrategyQueries.EXISTING_SHIPS, overlay.shipIds(), "One or more selected ships do not exist.");
        requireCompatibleBuilds(overlay);
        requireReferences(StrategyQueries.EXISTING_GUIDES, overlay.guideIds(), "One or more selected guides do not exist.");
        return overlay;
    }

    private void requireCompatibleBuilds(PreparedStrategyOverlay overlay) {
        if (overlay.buildIds().isEmpty()) return;
        Map<Long, Long> buildShips = new HashMap<>();
        for (Map<String, Object> row : repository.query(StrategyQueries.BUILD_SHIPS,
                Map.of("ids", overlay.buildIds()))) {
            buildShips.put(RowValues.longValue(row, "id"), RowValues.longValue(row, "ship_id"));
        }
        if (buildShips.size() != overlay.buildIds().size()) throw bad("One or more selected builds do not exist.");
        for (StrategyBuildReference reference : overlay.buildReferences()) {
            if (!Long.valueOf(reference.shipId()).equals(buildShips.get(reference.buildId()))) {
                throw bad("A selected build does not belong to the ship used by its marker.");
            }
        }
    }

    private void requireReferences(String sql, Set<Long> ids, String message) {
        if (!ids.isEmpty() && repository.count(sql, Map.of("ids", ids)) != ids.size()) throw bad(message);
    }

    private void replaceReferences(long id, PreparedStrategyOverlay overlay) {
        replace(id, "strategy_ship_references", "ship_id", overlay.shipIds());
        replace(id, "strategy_build_references", "build_id", overlay.buildIds());
        replace(id, "strategy_guide_references", "guide_id", overlay.guideIds());
    }

    private void replace(long id, String table, String column, Set<Long> values) {
        repository.update(StrategyQueries.REFERENCES_DELETE.formatted(table), Map.of("id", id));
        for (Long referenceId : values) repository.update(
                StrategyQueries.REFERENCE_INSERT.formatted(table, column), Map.of("id", id, "referenceId", referenceId));
    }

    private static Set<Long> fileIds(long first, long second) {
        Set<Long> result = new LinkedHashSet<>();
        result.add(first); result.add(second);
        return result;
    }

    private Map<String, Object> owned(long id, AuthenticatedUser actor) {
        return repository.optional(StrategyQueries.OWNED, Map.of("id", id, "ownerId", actor.id()))
                .orElseThrow(StrategyService::notFound);
    }

    private static String title(String value) {
        String result = value == null ? "" : value.strip();
        if (result.isEmpty()) throw bad("Strategy title is required.");
        return result;
    }
    private static String optional(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Strategy not found."); }
}
