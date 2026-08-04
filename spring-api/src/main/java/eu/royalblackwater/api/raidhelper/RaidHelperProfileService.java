package eu.royalblackwater.api.raidhelper;

import static eu.royalblackwater.api.persistence.RowValues.*;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.RaidHelperProfileCreate;
import eu.royalblackwater.api.contract.RaidHelperProfileRead;
import eu.royalblackwater.api.contract.RaidHelperProfileWrite;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.FernetSecretBox;
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
public class RaidHelperProfileService {
    private final JdbcQueryService jdbc;
    private final RaidHelperPolicy policy;
    private final FernetSecretBox secrets;
    private final AuditService audit;
    private final Clock clock;

    public RaidHelperProfileService(JdbcQueryService jdbc, RaidHelperPolicy policy, FernetSecretBox secrets,
                                    AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.policy = policy;
        this.secrets = secrets;
        this.audit = audit;
        this.clock = clock;
    }

    public List<RaidHelperProfileRead> list(AuthenticatedUser actor) {
        requireAdmin(actor);
        return jdbc.query("select * from raid_helper_profiles order by lower(name), id", Map.of())
                .stream().map(RaidHelperProfileService::read).toList();
    }

    @Transactional
    public RaidHelperProfileRead create(AuthenticatedUser actor, RaidHelperProfileCreate payload) {
        requireAdmin(actor);
        String apiKey = normalizedApiKey(payload.apiKey());
        LocalDateTime now = now();
        try {
            long id = jdbc.insertReturningId("""
                    insert into raid_helper_profiles
                      (name, server_id, api_key_encrypted, api_base_url, timezone, default_leader_id,
                       is_active, created_by_username, created_at, updated_at)
                    values (:name, :serverId, :apiKey, :baseUrl, :timezone, :leaderId,
                            :active, :username, :now, :now)
                    returning id
                    """, SqlParameters.ofNullable(
                    "name", policy.cleanName(payload.name(), "Profile name"),
                    "serverId", policy.numericIdentifier(payload.serverId(), "Server ID", true),
                    "apiKey", secrets.encrypt(apiKey),
                    "baseUrl", policy.baseUrl(payload.apiBaseUrl()),
                    "timezone", policy.timezone(payload.timezone()),
                    "leaderId", policy.numericIdentifier(payload.defaultLeaderId(), "Default leader ID", false),
                    "active", policy.flag(payload.isActive(), true),
                    "username", actor.username(), "now", now));
            audit.record(actor, "raid_helper_profile", id, "create",
                    "Raid-Helper profile created.", List.of("server_id", "api_key", "api_base_url", "timezone"));
            return get(id);
        } catch (DataIntegrityViolationException exception) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "A Raid-Helper profile with this name already exists.", exception);
        }
    }

    @Transactional
    public RaidHelperProfileRead update(AuthenticatedUser actor, long profileId, RaidHelperProfileWrite payload) {
        requireAdmin(actor);
        Map<String, Object> current = row(profileId);
        String serverId = policy.numericIdentifier(payload.serverId(), "Server ID", true);
        if (hasLinks(profileId) && !requiredString(current, "server_id").equals(serverId)) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "A profile with synchronized events cannot change its server ID; create a new profile instead.");
        }
        String encrypted = requiredString(current, "api_key_encrypted");
        if (payload.apiKey() != null && !payload.apiKey().isBlank()) {
            encrypted = secrets.encrypt(normalizedApiKey(payload.apiKey()));
        } else if (secrets.needsRotation(encrypted)) {
            encrypted = secrets.rotate(encrypted);
        }
        try {
            jdbc.update("""
                    update raid_helper_profiles set name=:name, server_id=:serverId,
                      api_key_encrypted=:apiKey, api_base_url=:baseUrl, timezone=:timezone,
                      default_leader_id=:leaderId, is_active=:active, updated_at=:now
                    where id=:id
                    """, SqlParameters.ofNullable(
                    "name", policy.cleanName(payload.name(), "Profile name"), "serverId", serverId,
                    "apiKey", encrypted, "baseUrl", policy.baseUrl(payload.apiBaseUrl()),
                    "timezone", policy.timezone(payload.timezone()),
                    "leaderId", policy.numericIdentifier(payload.defaultLeaderId(), "Default leader ID", false),
                    "active", policy.flag(payload.isActive(), true), "now", now(), "id", profileId));
            audit.record(actor, "raid_helper_profile", profileId, "update",
                    "Raid-Helper profile updated.", List.of("server_id", "api_key", "api_base_url", "timezone", "is_active"));
            return get(profileId);
        } catch (DataIntegrityViolationException exception) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "A Raid-Helper profile with this name already exists.", exception);
        }
    }

    @Transactional
    public void delete(AuthenticatedUser actor, long profileId) {
        requireAdmin(actor);
        row(profileId);
        if (hasLinks(profileId)) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "Profiles with synchronized calendar events cannot be deleted; deactivate them instead.");
        }
        jdbc.update("delete from raid_helper_profiles where id=:id", Map.of("id", profileId));
        audit.record(actor, "raid_helper_profile", profileId, "delete", "Raid-Helper profile deleted.", List.of());
    }

    public Map<String, Object> encryptedProfile(long profileId) {
        return row(profileId);
    }

    private RaidHelperProfileRead get(long id) {
        return read(row(id));
    }

    private Map<String, Object> row(long id) {
        return jdbc.optional("select * from raid_helper_profiles where id=:id", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Raid-Helper profile not found."));
    }

    private boolean hasLinks(long profileId) {
        return jdbc.count("""
                select count(*) from raid_helper_event_links l
                join raid_helper_destinations d on d.id=l.destination_id
                where d.profile_id=:id
                """, Map.of("id", profileId)) > 0;
    }

    private static RaidHelperProfileRead read(Map<String, Object> row) {
        return new RaidHelperProfileRead(requiredString(row, "api_base_url"),
                !requiredString(row, "api_key_encrypted").isBlank(), dateTime(row, "created_at"),
                requiredString(row, "created_by_username"), string(row, "default_leader_id"),
                longValue(row, "id"), booleanValue(row, "is_active"), requiredString(row, "name"),
                requiredString(row, "server_id"), requiredString(row, "timezone"), dateTime(row, "updated_at"));
    }

    private String normalizedApiKey(String raw) {
        String value = raw == null ? "" : raw.strip();
        if (value.regionMatches(true, 0, "Bearer ", 0, 7)) value = value.substring(7).strip();
        if (value.length() >= 2 && value.charAt(0) == value.charAt(value.length() - 1)
                && (value.charAt(0) == '\'' || value.charAt(0) == '"')) {
            value = value.substring(1, value.length() - 1).strip();
        }
        if (value.length() < 8 || value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0) {
            throw new ResponseStatusException(BAD_REQUEST, "Raid-Helper API key is empty or malformed.");
        }
        return value;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    static void requireAdmin(AuthenticatedUser actor) {
        if (!actor.isAdmin()) throw new ResponseStatusException(FORBIDDEN, "Admin access required.");
    }
}
