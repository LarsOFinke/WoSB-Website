package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.BuildRoleCreate;
import eu.royalblackwater.api.contract.BuildRoleRead;
import eu.royalblackwater.api.contract.BuildRoleUpdate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
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
    private final JdbcQueryService jdbc;
    private final AuditService audit;
    private final Clock clock;

    BuildRoleAdministrationService(JdbcQueryService jdbc, AuditService audit, Clock clock) {
        this.jdbc = jdbc; this.audit = audit; this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<BuildRoleRead> list() {
        return jdbc.query("select * from build_roles order by sort_order,lower(label),slug", Map.of())
                .stream().map(BuildRoleAdministrationService::read).toList();
    }

    @Transactional
    public BuildRoleRead create(BuildRoleCreate payload, AuthenticatedUser actor) {
        String slug = normalizeSlug(payload.slug());
        if (jdbc.count("select count(*) from build_roles where slug=:slug", Map.of("slug", slug)) > 0) {
            throw new ResponseStatusException(CONFLICT, "A build role with this slug already exists.");
        }
        LocalDateTime now = now();
        jdbc.update("""
                insert into build_roles(slug,label,description,sort_order,created_at,updated_at)
                values(:slug,:label,:description,:sortOrder,:now,:now)
                """, eu.royalblackwater.api.persistence.SqlParameters.ofNullable("slug", slug,
                "label", payload.label().strip(), "description", normalize(payload.description()),
                "sortOrder", payload.sortOrder() == null ? 100L : Math.max(0L, payload.sortOrder()), "now", now));
        audit.record(actor, "build_role", slug, "create", "Build role created.", List.of("slug", "label"));
        return required(slug);
    }

    @Transactional
    public BuildRoleRead update(String slug, BuildRoleUpdate payload, AuthenticatedUser actor) {
        String normalized = normalizeSlug(slug);
        if (jdbc.update("""
                update build_roles set label=:label,description=:description,sort_order=:sortOrder,updated_at=:now
                 where slug=:slug
                """, eu.royalblackwater.api.persistence.SqlParameters.ofNullable("label", payload.label().strip(),
                "description", normalize(payload.description()), "sortOrder", payload.sortOrder() == null ? 100L : Math.max(0L, payload.sortOrder()),
                "now", now(), "slug", normalized)) == 0) throw notFound();
        audit.record(actor, "build_role", normalized, "update", "Build role updated.", List.of("label", "description", "sort_order"));
        return required(normalized);
    }

    @Transactional
    public void delete(String slug, AuthenticatedUser actor) {
        String normalized = normalizeSlug(slug);
        if (jdbc.count("select count(*) from build_roles", Map.of()) <= 1) {
            throw new ResponseStatusException(BAD_REQUEST, "At least one build role must remain available.");
        }
        long usage = jdbc.count("select count(*) from builds where build_type=:slug", Map.of("slug", normalized));
        if (usage > 0) throw new ResponseStatusException(CONFLICT, "Build role is still assigned to " + usage + " build(s).");
        if (jdbc.update("delete from build_roles where slug=:slug", Map.of("slug", normalized)) == 0) throw notFound();
        audit.record(actor, "build_role", normalized, "delete", "Build role deleted.", List.of());
    }

    private BuildRoleRead required(String slug) {
        return jdbc.optional("select * from build_roles where slug=:slug", Map.of("slug", slug))
                .map(BuildRoleAdministrationService::read).orElseThrow(BuildRoleAdministrationService::notFound);
    }

    private static BuildRoleRead read(Map<String, Object> row) {
        return new BuildRoleRead(RowValues.dateTime(row, "created_at"), RowValues.string(row, "description"),
                RowValues.requiredString(row, "label"), RowValues.requiredString(row, "slug"),
                RowValues.longValue(row, "sort_order"), RowValues.dateTime(row, "updated_at"));
    }

    private static String normalizeSlug(String value) {
        String slug = value == null ? "" : value.strip().toLowerCase(Locale.ROOT);
        if (!slug.matches("[a-z0-9][a-z0-9_-]{0,31}")) throw new ResponseStatusException(BAD_REQUEST, "Invalid build role slug.");
        return slug;
    }
    private static String normalize(String value) { return value == null || value.isBlank() ? null : value.strip(); }
    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build role not found."); }
}
