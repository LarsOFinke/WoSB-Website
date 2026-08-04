package eu.royalblackwater.api.account;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.ModeratorCreate;
import eu.royalblackwater.api.contract.ModeratorCreateResponse;
import eu.royalblackwater.api.contract.UserAdministrationUpdate;
import eu.royalblackwater.api.contract.UserRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.PasswordHasher;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.FORBIDDEN;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class UserAdministrationService {
    private static final Set<String> ROLES = Set.of("user", "moderator", "admin");
    private final JdbcQueryService jdbc;
    private final UserDirectoryService directory;
    private final PasswordHasher passwords;
    private final AuditService audit;
    private final Clock clock;

    public UserAdministrationService(JdbcQueryService jdbc, UserDirectoryService directory,
                                     PasswordHasher passwords, AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.directory = directory;
        this.passwords = passwords;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<UserRead> list(UserAdministrationFilter filter) {
        return directory.list(filter);
    }

    @Transactional
    public UserRead update(long userId, UserAdministrationUpdate payload, AuthenticatedUser actor) {
        Map<String, Object> target = account(userId, true);
        Map<String, Object> actorRow = account(actor.id(), false);
        String currentRole = RowValues.requiredString(target, "role");
        String requestedRole = payload.role() == null ? currentRole : normalizedRole(payload.role());
        boolean requestedActive = payload.isActive() == null
                ? RowValues.booleanValue(target, "is_active") : payload.isActive();
        authorizeChange(target, actorRow, actor, requestedRole, requestedActive, payload);

        List<String> changed = new ArrayList<>();
        if (!requestedRole.equals(currentRole)) {
            long roleId = RowValues.longValue(jdbc.required(
                    "select id from site_roles where code=:code", Map.of("code", requestedRole)), "id");
            jdbc.update("update users set site_role_id=:roleId where id=:id", Map.of("roleId", roleId, "id", userId));
            changed.add("role");
        }
        if (requestedActive != RowValues.booleanValue(target, "is_active")) {
            jdbc.update("update users set is_active=:active where id=:id",
                    Map.of("active", requestedActive, "id", userId));
            changed.add("is_active");
        }
        if (!changed.isEmpty()) {
            jdbc.update("update users set updated_at=:now where id=:id", Map.of("now", now(), "id", userId));
            jdbc.update("delete from auth_sessions where user_id=:id", Map.of("id", userId));
            audit.record(actor, "user_account", userId, "update",
                    "Account “" + RowValues.requiredString(target, "username") + "” updated.", changed);
        }
        return directory.read(userId);
    }

    @Transactional
    public ModeratorCreateResponse createModerator(ModeratorCreate payload, AuthenticatedUser actor) {
        if (!actor.isAdmin()) throw forbidden("Only administrators can create moderator accounts.");
        String username = normalizeUsername(payload.username());
        String displayName = payload.displayName().strip();
        if (displayName.isEmpty()) throw bad("Display name is required.");
        if (payload.password().length() < 12 || payload.password().length() > 200) {
            throw bad("Password must contain between 12 and 200 characters.");
        }
        long duplicates = jdbc.count("""
                select (select count(*) from users where username=:username)
                     + (select count(*) from registration_requests where username=:username and status='pending')
                """, Map.of("username", username));
        if (duplicates > 0) throw bad("Username already exists or is waiting for review.");
        long roleId = RowValues.longValue(jdbc.required(
                "select id from site_roles where code='moderator'", Map.of()), "id");
        LocalDateTime now = now();
        long userId = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:passwordHash,:roleId,true,false,:now,:now) returning id
                """, Map.of("username", username, "passwordHash", passwords.hash(payload.password()),
                "roleId", roleId, "now", now));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                """, Map.of("userId", userId, "displayName", displayName, "now", now));
        audit.record(actor, "user_account", userId, "create", "Moderator account “" + username + "” created.",
                List.of("username", "display_name", "role", "is_active"));
        return new ModeratorCreateResponse(directory.read(userId));
    }

    private void authorizeChange(Map<String, Object> target, Map<String, Object> actorRow, AuthenticatedUser actor,
                                 String requestedRole, boolean requestedActive, UserAdministrationUpdate payload) {
        long targetId = RowValues.longValue(target, "id");
        String targetRole = RowValues.requiredString(target, "role");
        if (targetId == actor.id()) {
            if (!requestedActive) throw forbidden("You cannot deactivate your own account.");
            if (!requestedRole.equals(actor.role())) throw forbidden("You cannot change your own site role.");
        }
        if (RowValues.booleanValue(target, "is_bootstrap_admin") && targetId != actor.id()) {
            throw forbidden("The bootstrap administrator account cannot be modified by another account.");
        }
        boolean bootstrapDemotion = actor.canGrantAdmin() && "admin".equals(targetRole)
                && !RowValues.booleanValue(target, "is_bootstrap_admin")
                && payload.role() != null && !"admin".equals(requestedRole) && requestedActive;
        int targetRank = RowValues.intValue(target, "role_rank");
        int actorRank = RowValues.intValue(actorRow, "role_rank");
        if (targetId != actor.id() && targetRank >= actorRank && !bootstrapDemotion) {
            throw forbidden("You cannot modify an account with an equal or higher role.");
        }
        if (payload.role() != null) {
            if (!actor.isAdmin()) throw forbidden("Only administrators can change site roles.");
            if ("admin".equals(requestedRole) && !"admin".equals(targetRole) && !actor.canGrantAdmin()) {
                throw forbidden("Only the bootstrap administrator can grant administrator access.");
            }
            if ("admin".equals(targetRole) && !"admin".equals(requestedRole) && !actor.canGrantAdmin()) {
                throw forbidden("Only the bootstrap administrator can demote administrator accounts.");
            }
        }
        if ("admin".equals(requestedRole) && !requestedActive) {
            throw forbidden("Administrator accounts cannot be deactivated.");
        }
        if ("admin".equals(targetRole) && !requestedActive && activeAdminCount() <= 1) {
            throw forbidden("The last active administrator cannot be deactivated.");
        }
    }

    private long activeAdminCount() {
        return jdbc.count("""
                select count(*) from users u join site_roles r on r.id=u.site_role_id
                where r.code='admin' and u.is_active=true
                """, Map.of());
    }

    private Map<String, Object> account(long id, boolean lock) {
        return jdbc.optional("""
                select u.id,u.username,u.is_active,u.is_bootstrap_admin,r.code role,r.rank role_rank
                from users u join site_roles r on r.id=u.site_role_id where u.id=:id
                """ + (lock ? " for update" : ""), Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "User not found."));
    }

    private static String normalizedRole(String raw) {
        String role = raw.strip().toLowerCase(Locale.ROOT);
        if (!ROLES.contains(role)) throw bad("Invalid site role.");
        return role;
    }

    private static String normalizeUsername(String raw) {
        String username = raw.strip().toLowerCase(Locale.ROOT);
        if (username.length() < 3 || username.length() > 80 || username.chars().anyMatch(Character::isWhitespace)
                || username.chars().anyMatch(Character::isISOControl)) {
            throw bad("Username must contain 3 to 80 non-whitespace characters.");
        }
        return username;
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
    private static ResponseStatusException forbidden(String message) { return new ResponseStatusException(FORBIDDEN, message); }
}
