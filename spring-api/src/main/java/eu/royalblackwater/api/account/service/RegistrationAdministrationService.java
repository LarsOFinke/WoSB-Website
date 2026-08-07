package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.mapper.AccountDtoMapper;
import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.queries.RegistrationAdministrationQueries;
import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.RegistrationDecision;
import eu.royalblackwater.api.dto.RegistrationRequestRead;
import eu.royalblackwater.api.dto.UserRead;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
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
    private static final Set<String> STATUSES = Set.of("pending", "approved", "rejected", "all");
    private static final String REDACTED_HASH = "!reviewed-registration-secret-removed!";
    private final AccountDataRepository repository;
    private final UserDirectoryService users;
    private final AuditService audit;
    private final Clock clock;

    public RegistrationAdministrationService(AccountDataRepository repository, UserDirectoryService users,
                                             AuditService audit, Clock clock) {
        this.repository = repository;
        this.users = users;
        this.audit = audit;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public List<RegistrationRequestRead> list(String status, String search, LocalDate fromDate, LocalDate toDate) {
        String normalizedStatus = status == null ? "pending" : status.strip().toLowerCase(Locale.ROOT);
        if (!normalizedStatus.isEmpty() && !STATUSES.contains(normalizedStatus)) throw bad("Invalid registration status.");
        if ("all".equals(normalizedStatus)) normalizedStatus = "";
        StringBuilder sql = new StringBuilder(RegistrationAdministrationQueries.LIST_SELECT_01);
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (!normalizedStatus.isEmpty()) {
            sql.append(RegistrationAdministrationQueries.LIST_AND_01);
            parameters.put("status", normalizedStatus);
        }
        if (search != null && !search.isBlank()) {
            sql.append(RegistrationAdministrationQueries.LIST_AND_02);
            parameters.put("search", "%" + search.strip() + "%");
        }
        if (fromDate != null) {
            sql.append(RegistrationAdministrationQueries.LIST_AND_03);
            parameters.put("fromDate", LocalDateTime.of(fromDate, LocalTime.MIN));
        }
        if (toDate != null) {
            if (fromDate != null && toDate.isBefore(fromDate)) throw bad("to_date must not be before from_date.");
            sql.append(RegistrationAdministrationQueries.LIST_AND_04);
            parameters.put("toDate", LocalDateTime.of(toDate.plusDays(1), LocalTime.MIN));
        }
        sql.append(RegistrationAdministrationQueries.LIST_ORDER_BY_01);
        return mapRows(repository.query(sql.toString(), parameters));
    }

    @Transactional
    public RegistrationRequestRead approve(long requestId, RegistrationDecision payload, AuthenticatedUser actor) {
        Map<String, Object> request = pending(requestId);
        String username = RowValues.requiredString(request, "username");
        if (repository.count(RegistrationAdministrationQueries.APPROVE_SELECT_01, Map.of("username", username)) > 0) {
            throw bad("Username already exists.");
        }
        long userRoleId = roleId("user");
        LocalDateTime now = now();
        long userId = repository.insertReturningId(RegistrationAdministrationQueries.APPROVE_INSERT_01, Map.of("username", username, "passwordHash", RowValues.requiredString(request,"password_hash"),
                "roleId", userRoleId, "now", now));
        repository.update(RegistrationAdministrationQueries.APPROVE_INSERT_02, Map.of("userId", userId, "displayName", RowValues.requiredString(request,"display_name"),
                "now", now));
        if (RowValues.booleanValue(request, "wants_fleet_membership")) {
            createFleetApplication(request, userId, now);
        }
        repository.update(RegistrationAdministrationQueries.APPROVE_UPDATE_01, SqlParameters.ofNullable("note", normalizedNote(payload.note()), "actorId", actor.id(),
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
        repository.update(RegistrationAdministrationQueries.REJECT_UPDATE_01, SqlParameters.ofNullable("note", normalizedNote(payload.note()), "actorId", actor.id(),
                "now", now, "redacted", REDACTED_HASH, "id", requestId));
        audit.record(actor, "registration_request", requestId, "update",
                "Access request for “" + RowValues.requiredString(request,"username") + "” rejected.",
                List.of("status","decision_note","reviewed_by_id","reviewed_at"));
        return read(requestId);
    }

    @Transactional(readOnly = true)
    public RegistrationRequestRead read(long requestId) {
        Map<String, Object> row = repository.optional(RegistrationAdministrationQueries.READ_SELECT_01,
                Map.of("id", requestId)).orElseThrow(
                () -> new ResponseStatusException(NOT_FOUND, "Registration request not found."));
        return mapRows(List.of(row)).getFirst();
    }

    private Map<String, Object> pending(long id) {
        Map<String, Object> row = repository.optional(
                RegistrationAdministrationQueries.PENDING_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Registration request not found."));
        if (!"pending".equals(RowValues.string(row, "status"))) throw bad("Registration request is already reviewed.");
        return row;
    }

    private void createFleetApplication(Map<String, Object> request, long userId, LocalDateTime now) {
        Map<String, Object> fleet = repository.optional(RegistrationAdministrationQueries.CREATE_FLEET_APPLICATION_SELECT_01, Map.of()).orElseThrow(() -> bad("Official fleet not found; fleet application cannot be created."));
        long fleetId = RowValues.longValue(fleet, "id");
        Long requestedFleet = RowValues.nullableLong(request, "fleet_id");
        if (requestedFleet != null && requestedFleet != fleetId) {
            throw bad("Requested fleet is no longer the official fleet.");
        }
        long memberRole = RowValues.longValue(repository.required(
                RegistrationAdministrationQueries.CREATE_FLEET_APPLICATION_SELECT_02, Map.of()), "id");
        repository.update(RegistrationAdministrationQueries.CREATE_FLEET_APPLICATION_INSERT_01, SqlParameters.ofNullable("fleetId", fleetId, "userId", userId, "roleId", memberRole,
                "note", RowValues.string(request,"fleet_application_note"), "now", now));
    }

    private long roleId(String code) {
        return RowValues.longValue(repository.required(RegistrationAdministrationQueries.ROLE_ID_SELECT_01, Map.of("code", code)), "id");
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
        return rows.stream().map(row -> {
            Long createdUserId = RowValues.nullableLong(row, "created_user_id");
            Long reviewedById = RowValues.nullableLong(row, "reviewed_by_id");
            return AccountDtoMapper.registrationRequest(row,
                    referencedUser(userMap, createdUserId),
                    referencedUser(userMap, reviewedById));
        }).toList();
    }

    private static UserRead referencedUser(Map<Long, UserRead> userMap, Long userId) {
        return userId == null ? null : userMap.get(userId);
    }

    private static String normalizedNote(String note) {
        return note == null || note.isBlank() ? null : note.strip();
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static ResponseStatusException bad(String message) { return new ResponseStatusException(BAD_REQUEST, message); }
}
