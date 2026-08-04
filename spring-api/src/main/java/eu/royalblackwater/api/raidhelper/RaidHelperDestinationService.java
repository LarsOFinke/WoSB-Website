package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static eu.royalblackwater.api.raidhelper.RaidHelperProfileService.requireAdmin;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.RaidHelperDestinationRead;
import eu.royalblackwater.api.contract.RaidHelperDestinationWrite;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class RaidHelperDestinationService {
    private static final String BASE_QUERY = """
            select d.*, p.name profile_name, s.name squad_name
            from raid_helper_destinations d
            join raid_helper_profiles p on p.id=d.profile_id
            left join squads s on s.id=d.squad_id
            """;

    private final JdbcQueryService jdbc;
    private final RaidHelperPolicy policy;
    private final AuditService audit;
    private final Clock clock;

    public RaidHelperDestinationService(JdbcQueryService jdbc, RaidHelperPolicy policy,
                                        AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.policy = policy;
        this.audit = audit;
        this.clock = clock;
    }

    public List<RaidHelperDestinationRead> list(AuthenticatedUser actor) {
        requireAdmin(actor);
        return jdbc.query(BASE_QUERY + " order by lower(d.name), d.id", Map.of()).stream()
                .map(this::read).toList();
    }

    @Transactional
    public RaidHelperDestinationRead create(AuthenticatedUser actor, RaidHelperDestinationWrite payload) {
        requireAdmin(actor);
        ValidatedDestination value = validate(payload);
        LocalDateTime now = now();
        try {
            long id = jdbc.insertReturningId("""
                    insert into raid_helper_destinations
                      (profile_id, name, channel_id, scope_type, squad_id, is_default, is_active, created_at, updated_at)
                    values (:profileId, :name, :channelId, :scopeType, :squadId, :isDefault, :isActive, :now, :now)
                    returning id
                    """, value.parameters(now));
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
            jdbc.update("""
                    update raid_helper_destinations set profile_id=:profileId, name=:name,
                      channel_id=:channelId, scope_type=:scopeType, squad_id=:squadId,
                      is_default=:isDefault, is_active=:isActive, updated_at=:now
                    where id=:id
                    """, merge(value.parameters(now()), "id", destinationId));
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
        jdbc.update("delete from raid_helper_destinations where id=:id", Map.of("id", destinationId));
        audit.record(actor, "raid_helper_destination", destinationId, "delete",
                "Raid-Helper destination deleted.", List.of());
    }

    public Map<String, Object> detail(long destinationId) {
        return jdbc.optional(BASE_QUERY + " where d.id=:id", Map.of("id", destinationId))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper destination not found."));
    }

    private RaidHelperDestinationRead get(long id) {
        return read(detail(id));
    }

    private Map<String, Object> row(long id) {
        return jdbc.optional("select * from raid_helper_destinations where id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper destination not found."));
    }

    private RaidHelperDestinationRead read(Map<String, Object> row) {
        long id = longValue(row, "id");
        List<String> categories = jdbc.query("""
                select category from raid_helper_destination_categories
                where destination_id=:id order by category
                """, Map.of("id", id)).stream().map(value -> requiredString(value, "category")).toList();
        return new RaidHelperDestinationRead(categories, requiredString(row, "channel_id"),
                dateTime(row, "created_at"), id, booleanValue(row, "is_active"),
                booleanValue(row, "is_default"), requiredString(row, "name"),
                longValue(row, "profile_id"), requiredString(row, "profile_name"),
                requiredString(row, "scope_type"), nullableLong(row, "squad_id"),
                string(row, "squad_name"), dateTime(row, "updated_at"));
    }

    private ValidatedDestination validate(RaidHelperDestinationWrite payload) {
        if (jdbc.count("select count(*) from raid_helper_profiles where id=:id", Map.of("id", payload.profileId())) == 0) {
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
        if (squadId != null && jdbc.count("select count(*) from squads where id=:id and is_active=true", Map.of("id", squadId)) == 0) {
            throw new ResponseStatusException(BAD_REQUEST, "Squad not found or archived.");
        }
        return new ValidatedDestination(payload.profileId(), policy.cleanName(payload.name(), "Destination name"),
                policy.numericIdentifier(payload.channelId(), "Channel ID", true), scope, squadId,
                policy.categories(payload.categories()), policy.flag(payload.isDefault(), false),
                policy.flag(payload.isActive(), true));
    }

    private void replaceCategories(long id, List<String> categories) {
        jdbc.update("delete from raid_helper_destination_categories where destination_id=:id", Map.of("id", id));
        for (String category : categories) {
            jdbc.update("""
                    insert into raid_helper_destination_categories (destination_id, category)
                    values (:id, :category)
                    """, Map.of("id", id, "category", category));
        }
    }

    private boolean hasLinks(long id) {
        return jdbc.count("select count(*) from raid_helper_event_links where destination_id=:id", Map.of("id", id)) > 0;
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
