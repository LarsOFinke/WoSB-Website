package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.BuildCreate;
import eu.royalblackwater.api.contract.BuildOptionsCatalog;
import eu.royalblackwater.api.contract.BuildPage;
import eu.royalblackwater.api.contract.BuildRead;
import eu.royalblackwater.api.contract.BuildRoleRead;
import eu.royalblackwater.api.contract.BuildUpdate;
import eu.royalblackwater.api.contract.BuildVoteState;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class BuildService {
    private final BuildRepository repository;
    private final BuildValidationService validation;
    private final BuildAssembler assembler;
    private final JdbcQueryService jdbc;
    private final AuditService audit;
    private final Clock clock;

    BuildService(BuildRepository repository, BuildValidationService validation, BuildAssembler assembler,
                 JdbcQueryService jdbc, AuditService audit, Clock clock) {
        this.repository = repository;
        this.validation = validation;
        this.assembler = assembler;
        this.jdbc = jdbc;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public BuildPage list(String search, String type, String classification, long limit, long offset,
                          AuthenticatedUser viewer) {
        return assembler.page(repository.page(search, type, classification, null, (long) viewer.id(),
                boundedLimit(limit), Math.max(0, offset)));
    }

    @Transactional(readOnly = true)
    public BuildPage mine(String search, String type, String classification, long limit, long offset,
                          AuthenticatedUser actor) {
        return assembler.page(repository.page(search, type, classification, (long) actor.id(), (long) actor.id(),
                boundedLimit(limit), Math.max(0, offset)));
    }

    @Transactional(readOnly = true)
    public BuildRead get(long id, AuthenticatedUser viewer) {
        return assembler.detail(required(id, (long) viewer.id()));
    }

    @Transactional(readOnly = true)
    public List<BuildRead> getMany(List<Long> ids, AuthenticatedUser viewer) {
        List<Long> normalized = ids == null ? List.of() : ids.stream()
                .filter(java.util.Objects::nonNull)
                .filter(id -> id > 0)
                .distinct()
                .toList();
        List<BuildAggregate> aggregates = repository.findAll(normalized, (long) viewer.id());
        if (aggregates.size() != normalized.size()) throw notFound();
        return assembler.details(aggregates);
    }

    @Transactional(readOnly = true)
    public BuildOptionsCatalog options(Long shipId) { return assembler.options(shipId); }

    @Transactional(readOnly = true)
    public List<BuildRoleRead> roles() { return assembler.roles(); }

    @Transactional
    public BuildRead create(BuildCreate payload, AuthenticatedUser actor) {
        BuildPreparedPayload prepared = prepare(payload);
        long id = repository.create(prepared, actor.id());
        audit.record(actor, "build", id, "create", "Build created.", List.of("build_name", "ship_id", "slots"));
        return assembler.detail(required(id, (long) actor.id()));
    }

    @Transactional
    public BuildRead update(long id, BuildUpdate payload, AuthenticatedUser actor) {
        BuildPreparedPayload prepared = prepare(payload);
        if (!repository.updateOwned(id, actor.id(), prepared)) throw notFound();
        audit.record(actor, "build", id, "update", "Build updated.", List.of("build_name", "ship_id", "slots"));
        return assembler.detail(required(id, (long) actor.id()));
    }

    @Transactional
    public void deleteOwned(long id, AuthenticatedUser actor) {
        if (!repository.deleteOwned(id, actor.id())) throw notFound();
        audit.record(actor, "build", id, "delete", "Build deleted by owner.", List.of());
    }

    @Transactional
    public void deleteAny(long id, AuthenticatedUser actor) {
        if (!repository.deleteAny(id)) throw notFound();
        audit.record(actor, "build", id, "delete", "Build deleted by administrator.", List.of());
    }

    @Transactional
    public BuildVoteState vote(long id, AuthenticatedUser actor, boolean enabled) {
        if (repository.find(id, (long) actor.id()).isEmpty()) throw notFound();
        if (enabled) {
            jdbc.update("""
                    insert into build_votes(build_id,user_id,created_at) values(:buildId,:userId,:createdAt)
                    on conflict(build_id,user_id) do nothing
                    """, Map.of("buildId", id, "userId", actor.id(), "createdAt", now()));
        } else {
            jdbc.update("delete from build_votes where build_id=:buildId and user_id=:userId",
                    Map.of("buildId", id, "userId", actor.id()));
        }
        return voteState(id, actor.id());
    }

    @Transactional(readOnly = true)
    public List<BuildRead> allForAdministration(AuthenticatedUser actor) {
        return repository.page(null, null, null, null, (long) actor.id(), 1000, 0).items().stream()
                .map(assembler::detail).toList();
    }

    @Transactional
    public BuildRead assignRole(long id, String role, AuthenticatedUser actor) {
        if (jdbc.count("select count(*) from build_roles where slug=:slug", Map.of("slug", role)) == 0) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, "Build role not found.");
        }
        repository.assignRole(id, role);
        audit.record(actor, "build", id, "role_update", "Build role changed.", List.of("build_type"));
        return assembler.detail(required(id, (long) actor.id()));
    }

    private BuildPreparedPayload prepare(BuildCreate payload) {
        try { return validation.prepare(BuildPayload.from(payload)); }
        catch (IllegalArgumentException exception) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, exception.getMessage());
        }
    }

    private BuildPreparedPayload prepare(BuildUpdate payload) {
        try { return validation.prepare(BuildPayload.from(payload)); }
        catch (IllegalArgumentException exception) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, exception.getMessage());
        }
    }

    private BuildAggregate required(long id, Long viewerId) {
        return repository.find(id, viewerId).orElseThrow(BuildService::notFound);
    }

    private BuildVoteState voteState(long id, long userId) {
        long count = jdbc.count("select count(*) from build_votes where build_id=:id", Map.of("id", id));
        boolean selected = jdbc.count("select count(*) from build_votes where build_id=:id and user_id=:userId",
                Map.of("id", id, "userId", userId)) > 0;
        return new BuildVoteState(id, selected, count);
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static long boundedLimit(long value) { return Math.max(1, Math.min(value, 100)); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build not found."); }
}
