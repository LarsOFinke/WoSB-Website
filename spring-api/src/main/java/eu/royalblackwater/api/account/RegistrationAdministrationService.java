package eu.royalblackwater.api.account;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.RegistrationDecision;
import eu.royalblackwater.api.contract.RegistrationRequestRead;
import eu.royalblackwater.api.contract.UserRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class RegistrationAdministrationService {
    private static final Set<String> STATUSES = Set.of("pending", "approved", "rejected");
    private static final String REDACTED_HASH = "!reviewed-registration-secret-removed!";
    private final JdbcQueryService jdbc;
    private final UserDirectoryService users;
    private final AuditService audit;
    private final Clock clock;

    public RegistrationAdministrationService(JdbcQueryService jdbc, UserDirectoryService users,
                                             AuditService audit, Clock clock) {
        this.jdbc = jdbc;
        this.users = users;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<RegistrationRequestRead> list(String status, String search, LocalDate fromDate, LocalDate toDate) {
        String normalizedStatus = status == null ? "pending" : status.strip().toLowerCase(Locale.ROOT);
        if (!normalizedStatus.isEmpty() && !STATUSES.contains(normalizedStatus)) throw bad("Invalid registration status.");
        StringBuilder sql = new StringBuilder("select * from registration_requests where 1=1");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!normalizedStatus.isEmpty()) {
            sql.append(" and status=:status");
            parameters.put("status", normalizedStatus);
        }
        if (search != null && !search.isBlank()) {
            sql.append(" and (username ilike :search or display_name ilike :search or decision_note ilike :search)");
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (fromDate != null) {
            sql.append(" and created_at>=:fromDate");
            parameters.put("fromDate", LocalDateTime.of(fromDate, LocalTime.MIN));
        }
        if (toDate != null) {
            if (fromDate != null && toDate.isBefore(fromDate)) throw bad("to_date must not be before from_date.");
            sql.append(" and created_at<:toDate");
            parameters.put("toDate", LocalDateTime.of(toDate.plusDays(1), LocalTime.MIN));
        }
        sql.append(" order by created_at desc,id desc limit 250");
        return mapRows(jdbc.query(sql.toString(), parameters));
    }

    @Transactional
    public RegistrationRequestRead approve(long requestId, RegistrationDecision payload, AuthenticatedUser actor) {
        Map<String, Object> request = pending(requestId);
        String username = RowValues.requiredString(request, "username");
        if (jdbc.count("select count(*) from users where username=:username", Map.of("username", username)) > 0) {
            throw bad("Username already exists.");
        }
        long userRoleId = roleId("user");
        LocalDateTime now = now();
        long userId = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:passwordHash,:roleId,true,false,:now,:now) returning id
                """, Map.of("username", username, "passwordHash", RowValues.requiredString(request,"password_hash"),
                "roleId", userRoleId, "now", now));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                """, Map.of("userId", userId, "displayName", RowValues.requiredString(request,"display_name"),
                "now", now));
        if (RowValues.booleanValue(request, "wants_fleet_membership")) {
            createFleetApplication(request, userId, now);
        }
        jdbc.update("""
                update registration_requests set status='approved',decision_note=:note,reviewed_by_id=:actorId,
                    reviewed_at=:now,created_user_id=:userId,password_hash=:redacted,updated_at=:now where id=:id
                """, SqlParameters.ofNullable("note", normalizedNote(payload.note()), "actorId", actor.id(),
                "now", now, "userId", userId, "redacted", REDACTED_HASH, "id", requestId));
        audit.record(actor, "registration_request", requestId, "update",
                "Access request for “" + username + "” approved.",
                List.of("status","decision_note","reviewed_by_id","reviewed_at","created_user_id","fleet_membership"));
        return read(requestId);
    }

    @Transactional
    public RegistrationRequestRead reject(long requestId, RegistrationDecision payload, AuthenticatedUser actor) {
        Map<String, Object> request = pending(requestId);
        LocalDateTime now = now();
        jdbc.update("""
                update registration_requests set status='rejected',decision_note=:note,reviewed_by_id=:actorId,
                    reviewed_at=:now,password_hash=:redacted,updated_at=:now where id=:id
                """, SqlParameters.ofNullable("note", normalizedNote(payload.note()), "actorId", actor.id(),
                "now", now, "redacted", REDACTED_HASH, "id", requestId));
        audit.record(actor, "registration_request", requestId, "update",
                "Access request for “" + RowValues.requiredString(request,"username") + "” rejected.",
                List.of("status","decision_note","reviewed_by_id","reviewed_at"));
        return read(requestId);
    }

    @Transactional(readOnly = true)
    public RegistrationRequestRead read(long requestId) {
        Map<String, Object> row = jdbc.optional("select * from registration_requests where id=:id",
                Map.of("id", requestId)).orElseThrow(
                () -> new ResponseStatusException(NOT_FOUND, "Registration request not found."));
        return mapRows(List.of(row)).getFirst();
    }

    private Map<String, Object> pending(long id) {
        Map<String, Object> row = jdbc.optional(
                "select * from registration_requests where id=:id for update", Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Registration request not found."));
        if (!"pending".equals(RowValues.string(row, "status"))) throw bad("Registration request is already reviewed.");
        return row;
    }

    private void createFleetApplication(Map<String, Object> request, long userId, LocalDateTime now) {
        Map<String, Object> fleet = jdbc.optional("""
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """, Map.of()).orElseThrow(() -> bad("Official fleet not found; fleet application cannot be created."));
        long fleetId = RowValues.longValue(fleet, "id");
        Long requestedFleet = RowValues.nullableLong(request, "fleet_id");
        if (requestedFleet != null && requestedFleet != fleetId) {
            throw bad("Requested fleet is no longer the official fleet.");
        }
        long memberRole = RowValues.longValue(jdbc.required(
                "select id from fleet_roles where code='member' and is_active=true", Map.of()), "id");
        jdbc.update("""
                insert into fleet_memberships(fleet_id,user_id,fleet_role_id,status,note,joined_at,updated_at)
                values(:fleetId,:userId,:roleId,'pending',:note,:now,:now)
                """, SqlParameters.ofNullable("fleetId", fleetId, "userId", userId, "roleId", memberRole,
                "note", RowValues.string(request,"fleet_application_note"), "now", now));
    }

    private long roleId(String code) {
        return RowValues.longValue(jdbc.required("select id from site_roles where code=:code", Map.of("code", code)), "id");
    }

    private List<RegistrationRequestRead> mapRows(List<Map<String, Object>> rows) {
        Set<Long> referenced = new LinkedHashSet<>();
        for (Map<String, Object> row : rows) {
            Long reviewed = RowValues.nullableLong(row,"reviewed_by_id");
            Long created = RowValues.nullableLong(row,"created_user_id");
            if (reviewed != null) referenced.add(reviewed);
            if (created != null) referenced.add(created);
        }
        Map<Long, UserRead> userMap = users.readMany(new ArrayList<>(referenced));
        return rows.stream().map(row -> new RegistrationRequestRead(
                RowValues.dateTime(row,"created_at"),userMap.get(RowValues.nullableLong(row,"created_user_id")),
                RowValues.string(row,"decision_note"),RowValues.requiredString(row,"display_name"),
                RowValues.string(row,"fleet_application_note"),RowValues.nullableLong(row,"fleet_id"),
                RowValues.longValue(row,"id"),RowValues.nullableDateTime(row,"reviewed_at"),
                userMap.get(RowValues.nullableLong(row,"reviewed_by_id")),RowValues.requiredString(row,"status"),
                RowValues.dateTime(row,"updated_at"),RowValues.requiredString(row,"username"),
                RowValues.booleanValue(row,"wants_fleet_membership"))).toList();
    }

    private static String normalizedNote(String note) {
        return note == null || note.isBlank() ? null : note.strip();
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
