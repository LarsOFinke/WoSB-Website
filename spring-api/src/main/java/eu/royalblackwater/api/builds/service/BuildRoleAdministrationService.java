package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildRoleAdministrationQueries;
import eu.royalblackwater.api.dto.BuildRoleCreate;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildRoleUpdate;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.persistence.SqlParameters;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class BuildRoleAdministrationService {
    private final BuildDataRepository repository;
    private final AuditService audit;
    private final Clock clock;

    BuildRoleAdministrationService(BuildDataRepository repository, AuditService audit, Clock clock) {
        this.repository = repository; this.audit = audit; this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<BuildRoleRead> list() {
        return repository.query(BuildRoleAdministrationQueries.LIST_SELECT_01, Map.of())
                .stream().map(BuildDtoMapper::role).toList();
    }

    @Transactional
    public BuildRoleRead create(BuildRoleCreate payload, AuthenticatedUser actor) {
        String slug = normalizeSlug(payload.slug());
        if (repository.count(BuildRoleAdministrationQueries.CREATE_SELECT_01, Map.of("slug", slug)) > 0) {
            throw new ResponseStatusException(CONFLICT, "A build role with this slug already exists.");
        }
        LocalDateTime now = UtcDateTimes.now(clock);
        repository.update(BuildRoleAdministrationQueries.CREATE_INSERT_01, SqlParameters.ofNullable("slug", slug,
                "label", payload.label().strip(), "description", normalize(payload.description()),
                "sortOrder", payload.sortOrder() == null ? 100L : Math.max(0L, payload.sortOrder()), "now", now));
        audit.record(actor, "build_role", slug, "create", "Build role created.", List.of("slug", "label"));
        return required(slug);
    }

    @Transactional
    public BuildRoleRead update(String slug, BuildRoleUpdate payload, AuthenticatedUser actor) {
        String normalized = normalizeSlug(slug);
        if (repository.update(BuildRoleAdministrationQueries.UPDATE_UPDATE_01, SqlParameters.ofNullable("label", payload.label().strip(),
                "description", normalize(payload.description()), "sortOrder", payload.sortOrder() == null ? 100L : Math.max(0L, payload.sortOrder()),
                "now", UtcDateTimes.now(clock), "slug", normalized)) == 0) throw notFound();
        audit.record(actor, "build_role", normalized, "update", "Build role updated.", List.of("label", "description", "sort_order"));
        return required(normalized);
    }

    @Transactional
    public void delete(String slug, AuthenticatedUser actor) {
        String normalized = normalizeSlug(slug);
        if (repository.count(BuildRoleAdministrationQueries.DELETE_SELECT_01, Map.of()) <= 1) {
            throw new ResponseStatusException(BAD_REQUEST, "At least one build role must remain available.");
        }
        long usage = repository.count(BuildRoleAdministrationQueries.DELETE_SELECT_02, Map.of("slug", normalized));
        if (usage > 0) throw new ResponseStatusException(CONFLICT, "Build role is still assigned to " + usage + " build(s).");
        if (repository.update(BuildRoleAdministrationQueries.DELETE_DELETE_01, Map.of("slug", normalized)) == 0) throw notFound();
        audit.record(actor, "build_role", normalized, "delete", "Build role deleted.", List.of());
    }

    private BuildRoleRead required(String slug) {
        return repository.optional(BuildRoleAdministrationQueries.REQUIRED_SELECT_01, Map.of("slug", slug))
                .map(BuildDtoMapper::role).orElseThrow(BuildRoleAdministrationService::notFound);
    }


    private static String normalizeSlug(String value) {
        String slug = value == null ? "" : value.strip().toLowerCase(Locale.ROOT);
        if (!slug.matches("[a-z0-9][a-z0-9_-]{0,31}")) throw new ResponseStatusException(BAD_REQUEST, "Invalid build role slug.");
        return slug;
    }
    private static String normalize(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build role not found."); }
}
