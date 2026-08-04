package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.DataSubjectRequestRead;
import eu.royalblackwater.api.contract.DataSubjectRequestResolve;
import eu.royalblackwater.api.contract.PrivacyContactRead;
import eu.royalblackwater.api.contract.PrivacyContactResolve;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.PasswordHasher;
import java.security.SecureRandom;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY;

@Service
public class PrivacyAdministrationService {
    private static final Set<String> DECISIONS = Set.of("complete", "reject");
    private static final Pattern SQL_IDENTIFIER = Pattern.compile("[a-z][a-z0-9_]*");
    private final JdbcQueryService jdbc;
    private final PasswordHasher passwords;
    private final AuditService audit;
    private final SecureRandom random;
    private final Clock clock;

    public PrivacyAdministrationService(JdbcQueryService jdbc, PasswordHasher passwords,
                                        AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.passwords = passwords;
        this.audit = audit;
        this.random = new SecureRandom();
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<DataSubjectRequestRead> listRequests() {
        return jdbc.query("""
                select r.id,r.subject_user_id,u.username subject_username,r.request_type,r.status,
                       r.details,r.resolution_note,r.handled_by_user_id,r.created_at,r.resolved_at
                from data_subject_requests r join users u on u.id=r.subject_user_id
                order by case when r.status='pending' then 0 else 1 end,r.created_at asc,r.id asc
                limit 250
                """, Map.of()).stream().map(PrivacyAdministrationService::requestRead).toList();
    }

    @Transactional(readOnly = true)
    public List<PrivacyContactRead> listContacts() {
        return jdbc.query("""
                select id,user_id,reply_email,subject,message,status,resolution_note,handled_by_user_id,
                       created_at,resolved_at
                from privacy_contact_requests
                order by case when status='pending' then 0 else 1 end,created_at asc,id asc
                limit 250
                """, Map.of()).stream().map(PrivacyAdministrationService::contactRead).toList();
    }

    @Transactional
    public PrivacyContactRead resolveContact(long id, PrivacyContactResolve payload, AuthenticatedUser actor) {
        String decision = decision(payload.decision());
        Map<String, Object> row = jdbc.optional(
                "select * from privacy_contact_requests where id=:id for update", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Privacy contact request not found."));
        requirePending(row, "Privacy contact request has already been resolved.");
        jdbc.update("""
                update privacy_contact_requests set status=:status,resolution_note=:note,
                    handled_by_user_id=:actorId,resolved_at=:resolvedAt where id=:id
                """, Map.of("status", status(decision), "note", payload.resolutionNote().strip(),
                "actorId", actor.id(), "resolvedAt", now(), "id", id));
        audit.record(actor, "privacy_contact_request", id, decision,
                "Privacy contact request resolved.", List.of("status", "resolution_note"));
        return contactRead(jdbc.required("select * from privacy_contact_requests where id=:id", Map.of("id", id)));
    }

    @Transactional
    public DataSubjectRequestRead resolveRequest(long id, DataSubjectRequestResolve payload, AuthenticatedUser actor) {
        String decision = decision(payload.decision());
        Map<String, Object> row = jdbc.optional("""
                select r.*,u.username subject_username,u.is_bootstrap_admin
                from data_subject_requests r join users u on u.id=r.subject_user_id
                where r.id=:id for update of r,u
                """, Map.of("id", id)).orElseThrow(
                () -> new ResponseStatusException(NOT_FOUND, "Privacy request not found."));
        requirePending(row, "Privacy request has already been resolved.");
        if ("complete".equals(decision) && "deletion".equals(RowValues.string(row, "request_type"))) {
            pseudonymize(RowValues.longValue(row, "subject_user_id"), row);
        }
        jdbc.update("""
                update data_subject_requests set status=:status,resolution_note=:note,
                    handled_by_user_id=:actorId,resolved_at=:resolvedAt where id=:id
                """, Map.of("status", status(decision), "note", payload.resolutionNote().strip(),
                "actorId", actor.id(), "resolvedAt", now(), "id", id));
        audit.record(actor, "privacy_request", id, decision,
                "Privacy " + RowValues.string(row, "request_type") + " request resolved.",
                List.of("status", "resolution_note"));
        return requestRead(jdbc.required("""
                select r.id,r.subject_user_id,u.username subject_username,r.request_type,r.status,
                       r.details,r.resolution_note,r.handled_by_user_id,r.created_at,r.resolved_at
                from data_subject_requests r join users u on u.id=r.subject_user_id where r.id=:id
                """, Map.of("id", id)));
    }

    private void pseudonymize(long userId, Map<String, Object> userRow) {
        if (RowValues.booleanValue(userRow, "is_bootstrap_admin")) {
            throw new ResponseStatusException(CONFLICT, "The bootstrap administrator cannot be deleted.");
        }
        String oldUsername = RowValues.requiredString(userRow, "subject_username");
        String newUsername = uniqueDeletedUsername(userId);
        String replacementPassword = passwords.hash(randomSecret());
        jdbc.update("delete from auth_sessions where user_id=:id", Map.of("id", userId));
        jdbc.update("delete from fleet_memberships where user_id=:id", Map.of("id", userId));
        jdbc.update("delete from group_members where user_id=:id", Map.of("id", userId));
        jdbc.update("delete from build_votes where user_id=:id", Map.of("id", userId));
        jdbc.update("delete from user_profiles where user_id=:id", Map.of("id", userId));
        jdbc.update("""
                update privacy_contact_requests set user_id=null,reply_email='deleted@example.invalid',
                    message='[removed with account deletion]' where user_id=:id
                """, Map.of("id", userId));
        nullNullableUserReferences(userId);
        jdbc.update("update audit_logs set actor_username='[deleted user]' where actor_username=:username",
                Map.of("username", oldUsername));
        jdbc.update("""
                update users set username=:username,password_hash=:passwordHash,is_active=false,updated_at=:updatedAt
                where id=:id
                """, Map.of("username", newUsername, "passwordHash", replacementPassword,
                "updatedAt", now(), "id", userId));
    }

    private void nullNullableUserReferences(long userId) {
        List<Map<String, Object>> references = jdbc.query("""
                select tc.table_name,kcu.column_name
                from information_schema.table_constraints tc
                join information_schema.key_column_usage kcu
                  on tc.constraint_schema=kcu.constraint_schema and tc.constraint_name=kcu.constraint_name
                join information_schema.constraint_column_usage ccu
                  on tc.constraint_schema=ccu.constraint_schema and tc.constraint_name=ccu.constraint_name
                join information_schema.columns cols
                  on cols.table_schema=tc.table_schema and cols.table_name=tc.table_name
                 and cols.column_name=kcu.column_name
                where tc.constraint_type='FOREIGN KEY' and tc.table_schema=current_schema()
                  and ccu.table_name='users' and ccu.column_name='id' and cols.is_nullable='YES'
                """, Map.of());
        for (Map<String, Object> reference : references) {
            String table = RowValues.requiredString(reference, "table_name");
            String column = RowValues.requiredString(reference, "column_name");
            if (!SQL_IDENTIFIER.matcher(table).matches() || !SQL_IDENTIFIER.matcher(column).matches()) {
                throw new IllegalStateException("Unsafe user reference metadata encountered.");
            }
            jdbc.update("update " + table + " set " + column + "=null where " + column + "=:id",
                    Map.of("id", userId));
        }
    }

    private String uniqueDeletedUsername(long userId) {
        for (int attempt = 0; attempt < 5; attempt++) {
            byte[] suffix = new byte[4];
            random.nextBytes(suffix);
            String candidate = "deleted-" + userId + "-" + HexFormat.of().formatHex(suffix);
            if (jdbc.count("select count(*) from users where username=:username", Map.of("username", candidate)) == 0) {
                return candidate;
            }
        }
        throw new IllegalStateException("Could not allocate a pseudonymous username.");
    }

    private String randomSecret() {
        byte[] value = new byte[48];
        random.nextBytes(value);
        return java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }

    private static String decision(String raw) {
        String value = raw == null ? "" : raw.strip().toLowerCase(Locale.ROOT);
        if (!DECISIONS.contains(value)) {
            throw new ResponseStatusException(UNPROCESSABLE_ENTITY, "Decision must be complete or reject.");
        }
        return value;
    }

    private static String status(String decision) {
        return "complete".equals(decision) ? "completed" : "rejected";
    }

    private static void requirePending(Map<String, Object> row, String message) {
        if (!"pending".equals(RowValues.string(row, "status"))) {
            throw new ResponseStatusException(CONFLICT, message);
        }
    }

    private static DataSubjectRequestRead requestRead(Map<String, Object> row) {
        return new DataSubjectRequestRead(RowValues.dateTime(row,"created_at"),RowValues.string(row,"details"),
                RowValues.nullableLong(row,"handled_by_user_id"),RowValues.longValue(row,"id"),
                RowValues.requiredString(row,"request_type"),RowValues.string(row,"resolution_note"),
                RowValues.nullableDateTime(row,"resolved_at"),RowValues.requiredString(row,"status"),
                RowValues.longValue(row,"subject_user_id"),RowValues.requiredString(row,"subject_username"));
    }

    private static PrivacyContactRead contactRead(Map<String, Object> row) {
        return new PrivacyContactRead(RowValues.dateTime(row,"created_at"),
                RowValues.nullableLong(row,"handled_by_user_id"),RowValues.longValue(row,"id"),
                RowValues.requiredString(row,"message"),RowValues.requiredString(row,"reply_email"),
                RowValues.string(row,"resolution_note"),RowValues.nullableDateTime(row,"resolved_at"),
                RowValues.requiredString(row,"status"),RowValues.requiredString(row,"subject"),
                RowValues.nullableLong(row,"user_id"));
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
}
