package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.filter.UserAdministrationFilter;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.queries.UserAdministrationQueries;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.ModeratorCreate;
import eu.royalblackwater.api.dto.ModeratorCreateResponse;
import eu.royalblackwater.api.dto.UserAdministrationUpdate;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
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
    private final AccountDataRepository repository;
    private final UserDirectoryService directory;
    private final PasswordHasher passwords;
    private final AuditService audit;
    private final Clock clock;

    public UserAdministrationService(AccountDataRepository repository, UserDirectoryService directory,
                                     PasswordHasher passwords, AuditService audit, Clock clock) {
        this.repository = repository;
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
            long roleId = RowValues.longValue(repository.required(
                    UserAdministrationQueries.UPDATE_SELECT_01, Map.of("code", requestedRole)), "id");
            repository.update(UserAdministrationQueries.UPDATE_UPDATE_01, Map.of("roleId", roleId, "id", userId));
            changed.add("role");
        }
        if (requestedActive != RowValues.booleanValue(target, "is_active")) {
            repository.update(UserAdministrationQueries.UPDATE_UPDATE_02,
                    Map.of("active", requestedActive, "id", userId));
            changed.add("is_active");
        }
        if (!changed.isEmpty()) {
            repository.update(UserAdministrationQueries.UPDATE_UPDATE_03, Map.of("now", now(), "id", userId));
            repository.update(UserAdministrationQueries.UPDATE_DELETE_01, Map.of("id", userId));
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
        long duplicates = repository.count(UserAdministrationQueries.CREATE_MODERATOR_SELECT_01, Map.of("username", username));
        if (duplicates > 0) throw bad("Username already exists or is waiting for review.");
        long roleId = RowValues.longValue(repository.required(
                UserAdministrationQueries.CREATE_MODERATOR_SELECT_02, Map.of()), "id");
        LocalDateTime now = now();
        long userId = repository.insertReturningId(UserAdministrationQueries.CREATE_MODERATOR_INSERT_01, Map.of("username", username, "passwordHash", passwords.hash(payload.password()),
                "roleId", roleId, "now", now));
        repository.update(UserAdministrationQueries.CREATE_MODERATOR_INSERT_02, Map.of("userId", userId, "displayName", displayName, "now", now));
        audit.record(actor, "user_account", userId, "create", "Moderator account “" + username + "” created.",
                List.of("username", "display_name", "role", "is_active"));
        return AccountDtoMapper.moderatorCreated(directory.read(userId));
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
        return repository.count(UserAdministrationQueries.ACTIVE_ADMIN_COUNT_SELECT_01, Map.of());
    }

    private Map<String, Object> account(long id, boolean lock) {
        return repository.optional(UserAdministrationQueries.ACCOUNT_SELECT_01 + (lock ? " for update" : ""), Map.of("id", id))
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
