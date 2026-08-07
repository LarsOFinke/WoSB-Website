package eu.royalblackwater.api.raidhelper.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.RaidHelperDestinationRead;
import eu.royalblackwater.api.dto.RaidHelperDestinationWrite;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.raidhelper.mapper.RaidHelperDtoMapper;
import eu.royalblackwater.api.raidhelper.repository.RaidHelperRepository;
import eu.royalblackwater.api.raidhelper.repository.queries.RaidHelperDestinationQueries;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.raidhelper.service.RaidHelperProfileService.requireAdmin;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class RaidHelperDestinationService {

    private final RaidHelperRepository repository;
    private final RaidHelperPolicy policy;
    private final AuditService audit;
    private final Clock clock;
    private final RaidHelperDtoMapper mapper;

    public RaidHelperDestinationService(RaidHelperRepository repository, RaidHelperPolicy policy,
                                        AuditService audit, Clock clock, RaidHelperDtoMapper mapper) {
        this.repository = repository;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
        this.mapper = mapper;
    }

    public List<RaidHelperDestinationRead> list(AuthenticatedUser actor) {
        requireAdmin(actor);
        return repository.query(RaidHelperDestinationQueries.BASE_QUERY + RaidHelperDestinationQueries.LIST_ORDER_BY_01, Map.of()).stream()
                .map(this::toRead).toList();
    }

    @Transactional
    public RaidHelperDestinationRead create(AuthenticatedUser actor, RaidHelperDestinationWrite payload) {
        requireAdmin(actor);
        ValidatedDestination value = validate(payload);
        LocalDateTime now = now();
        try {
            long id = repository.insertReturningId(RaidHelperDestinationQueries.CREATE_INSERT_01, value.parameters(now));
            replaceCategories(id, value.categories());
            audit.record(actor, "raid_helper_destination", id, "create", "Raid-Helper destination created.",
                    List.of("profile_id", "channel_id", "scope_type", "squad_id", "categories", "is_default", "is_active"));
            return get(id);
        } catch (DataIntegrityViolationException exception) {
            throw duplicate(exception);
        }
    }

    @Transactional
    public RaidHelperDestinationRead update(
            AuthenticatedUser actor, long destinationId, RaidHelperDestinationWrite payload) {
        requireAdmin(actor);
        Map<String, Object> current = row(destinationId);
        ValidatedDestination value = validate(payload);
        if (hasLinks(destinationId) && targetChanged(current, value)) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "A destination with synchronized events cannot change profile, channel or scope; create a new destination instead.");
        }
        try {
            repository.update(RaidHelperDestinationQueries.UPDATE_UPDATE_01, merge(value.parameters(now()), "id", destinationId));
            replaceCategories(destinationId, value.categories());
            audit.record(actor, "raid_helper_destination", destinationId, "update", "Raid-Helper destination updated.",
                    List.of("profile_id", "channel_id", "scope_type", "squad_id", "categories", "is_default", "is_active"));
            return get(destinationId);
        } catch (DataIntegrityViolationException exception) {
            throw duplicate(exception);
        }
    }

    @Transactional
    public void delete(AuthenticatedUser actor, long destinationId) {
        requireAdmin(actor);
        row(destinationId);
        if (hasLinks(destinationId)) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "Destinations with synchronized events cannot be deleted; deactivate them instead.");
        }
        repository.update(RaidHelperDestinationQueries.DELETE_DELETE_01, Map.of("id", destinationId));
        audit.record(actor, "raid_helper_destination", destinationId, "delete",
                "Raid-Helper destination deleted.", List.of());
    }

    public RaidHelperDestinationRead read(long destinationId) {
        return toRead(detailRow(destinationId));
    }

    private RaidHelperDestinationRead get(long id) {
        return toRead(detailRow(id));
    }

    private Map<String, Object> detailRow(long destinationId) {
        return repository.optional(RaidHelperDestinationQueries.BASE_QUERY + RaidHelperDestinationQueries.DETAIL_WHERE_01, Map.of("id", destinationId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper destination not found."));
    }

    private Map<String, Object> row(long id) {
        return repository.optional(RaidHelperDestinationQueries.ROW_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper destination not found."));
    }

    private RaidHelperDestinationRead toRead(Map<String, Object> row) {
        long id = longValue(row, "id");
        List<String> categories = repository.query(RaidHelperDestinationQueries.READ_SELECT_01, Map.of("id", id)).stream().map(value -> requiredString(value, "category")).toList();
        return mapper.destinationRead(row, categories);
    }

    private ValidatedDestination validate(RaidHelperDestinationWrite payload) {
        if (repository.count(RaidHelperDestinationQueries.VALIDATE_SELECT_01, Map.of("id", payload.profileId())) == 0) {
            throw new ResponseStatusException(BAD_REQUEST, "Raid-Helper profile not found.");
        }
        String scope = payload.scopeType() == null ? "" : payload.scopeType().strip().toLowerCase();
        if (!SetHolder.SCOPES.contains(scope)) throw new ResponseStatusException(BAD_REQUEST, "Invalid destination scope.");
        Long squadId = payload.squadId();
        if ("fleet".equals(scope) && squadId != null) {
            throw new ResponseStatusException(BAD_REQUEST, "Fleet destinations cannot reference a squad.");
        }
        if ("squad".equals(scope) && squadId == null) {
            throw new ResponseStatusException(BAD_REQUEST, "Squad destinations require a squad.");
        }
        if (squadId != null && repository.count(RaidHelperDestinationQueries.VALIDATE_SELECT_02, Map.of("id", squadId)) == 0) {
            throw new ResponseStatusException(BAD_REQUEST, "Squad not found or archived.");
        }
        return new ValidatedDestination(payload.profileId(), policy.cleanName(payload.name(), "Destination name"),
                policy.numericIdentifier(payload.channelId(), "Channel ID", true), scope, squadId,
                policy.categories(payload.categories()), policy.flag(payload.isDefault(), false),
                policy.flag(payload.isActive(), true));
    }

    private void replaceCategories(long id, List<String> categories) {
        repository.update(RaidHelperDestinationQueries.REPLACE_CATEGORIES_DELETE_01, Map.of("id", id));
        for (String category : categories) {
            repository.update(RaidHelperDestinationQueries.REPLACE_CATEGORIES_INSERT_01, Map.of("id", id, "category", category));
        }
    }

    private boolean hasLinks(long id) {
        return repository.count(RaidHelperDestinationQueries.HAS_LINKS_SELECT_01, Map.of("id", id)) > 0;
    }

    private static boolean targetChanged(Map<String, Object> current, ValidatedDestination value) {
        return longValue(current, "profile_id") != value.profileId()
                || !requiredString(current, "channel_id").equals(value.channelId())
                || !requiredString(current, "scope_type").equals(value.scopeType())
                || !java.util.Objects.equals(nullableLong(current, "squad_id"), value.squadId());
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
                "This profile, channel and scope combination already exists.", exception);
    }

    private record ValidatedDestination(long profileId, String name, String channelId, String scopeType,
                                        Long squadId, List<String> categories, boolean isDefault, boolean isActive) {
        Map<String, Object> parameters(LocalDateTime now) {
            return SqlParameters.ofNullable("profileId", profileId, "name", name, "channelId", channelId,
                    "scopeType", scopeType, "squadId", squadId, "isDefault", isDefault,
                    "isActive", isActive, "now", now);
        }
    }

    private static final class SetHolder {
        private static final java.util.Set<String> SCOPES = java.util.Set.of("fleet", "squad");
    }
}
