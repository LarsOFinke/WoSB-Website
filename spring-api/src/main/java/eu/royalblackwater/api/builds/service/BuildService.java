package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.core.util.UtcDateTimes;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.builds.mapper.BuildAssembler;
import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.dto.BuildAggregate;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildPreparedPayload;
import eu.royalblackwater.api.builds.repository.BuildDataRepository;
import eu.royalblackwater.api.builds.repository.BuildRepository;
import eu.royalblackwater.api.builds.repository.queries.BuildQueries;
import eu.royalblackwater.api.dto.BuildCreate;
import eu.royalblackwater.api.dto.BuildOptionsCatalog;
import eu.royalblackwater.api.dto.BuildPage;
import eu.royalblackwater.api.dto.BuildRead;
import eu.royalblackwater.api.dto.BuildRoleRead;
import eu.royalblackwater.api.dto.BuildUpdate;
import eu.royalblackwater.api.dto.BuildVoteState;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class BuildService {
    private final BuildRepository builds;
    private final BuildValidationService validation;
    private final BuildAssembler assembler;
    private final BuildDataRepository data;
    private final BuildPrintoutService printouts;
    private final AuditService audit;
    private final Clock clock;

    public BuildService(BuildRepository builds, BuildValidationService validation, BuildAssembler assembler,
                        BuildDataRepository data, BuildPrintoutService printouts, AuditService audit, Clock clock) {
        this.builds = builds;
        this.validation = validation;
        this.assembler = assembler;
        this.data = data;
        this.printouts = printouts;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public BuildPage list(String search, String type, String classification, Long shipRate, long limit, long offset,
                          AuthenticatedUser viewer) {
        return assembler.page(builds.page(search, type, classification, shipRate, null, (long) viewer.id(),
                boundedLimit(limit), Math.max(0, offset)));
    }

    @Transactional(readOnly = true)
    public BuildPage mine(String search, String type, String classification, Long shipRate, long limit, long offset,
                          AuthenticatedUser actor) {
        return assembler.page(builds.page(search, type, classification, shipRate, (long) actor.id(), (long) actor.id(),
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
        List<BuildAggregate> aggregates = builds.findAll(normalized, (long) viewer.id());
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
        long id = builds.create(prepared, actor.id());
        audit.record(actor, "build", id, "create", "Build created.", List.of("build_name", "ship_id", "slots"));
        return assembler.detail(required(id, (long) actor.id()));
    }

    @Transactional
    public BuildRead update(long id, BuildUpdate payload, AuthenticatedUser actor) {
        BuildPreparedPayload prepared = prepare(payload);
        if (!builds.updateOwned(id, actor.id(), prepared)) throw notFound();
        printouts.invalidate(id);
        audit.record(actor, "build", id, "update", "Build updated.", List.of("build_name", "ship_id", "slots"));
        return assembler.detail(required(id, (long) actor.id()));
    }

    @Transactional
    public void deleteOwned(long id, AuthenticatedUser actor) {
        if (!builds.deleteOwned(id, actor.id())) throw notFound();
        printouts.deleteAfterBuildCommit(id);
        audit.record(actor, "build", id, "delete", "Build deleted by owner.", List.of());
    }

    @Transactional
    public void deleteAny(long id, AuthenticatedUser actor) {
        if (!builds.deleteAny(id)) throw notFound();
        printouts.deleteAfterBuildCommit(id);
        audit.record(actor, "build", id, "delete", "Build deleted by administrator.", List.of());
    }

    @Transactional
    public BuildVoteState vote(long id, AuthenticatedUser actor, boolean enabled) {
        if (builds.find(id, (long) actor.id()).isEmpty()) throw notFound();
        if (enabled) {
            data.update(BuildQueries.VOTE_INSERT_01, Map.of("buildId", id, "userId", actor.id(), "createdAt", UtcDateTimes.now(clock)));
        } else {
            data.update(BuildQueries.VOTE_DELETE_01,
                    Map.of("buildId", id, "userId", actor.id()));
        }
        return voteState(id, actor.id());
    }

    @Transactional(readOnly = true)
    public List<BuildRead> allForAdministration(AuthenticatedUser actor) {
        return builds.page(null, null, null, null, null, (long) actor.id(), 1000, 0).items().stream()
                .map(assembler::detail).toList();
    }

    @Transactional
    public BuildRead assignRole(long id, String role, AuthenticatedUser actor) {
        if (data.count(BuildQueries.ASSIGN_ROLE_SELECT_01, Map.of("slug", role)) == 0) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST, "Build role not found.");
        }
        builds.assignRole(id, role);
        printouts.invalidate(id);
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
        return builds.find(id, viewerId).orElseThrow(BuildService::notFound);
    }

    private BuildVoteState voteState(long id, long userId) {
        long count = data.count(BuildQueries.VOTE_STATE_SELECT_01, Map.of("id", id));
        boolean selected = data.count(BuildQueries.VOTE_STATE_SELECT_02,
                Map.of("id", id, "userId", userId)) > 0;
        return BuildDtoMapper.voteState(id, selected, count);
    }
    private static long boundedLimit(long value) { return Math.max(1, Math.min(value, 100)); }
    private static ResponseStatusException notFound() { return new ResponseStatusException(NOT_FOUND, "Build not found."); }
}
