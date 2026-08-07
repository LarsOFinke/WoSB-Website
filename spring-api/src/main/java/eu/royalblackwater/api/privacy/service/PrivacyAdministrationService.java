package eu.royalblackwater.api.privacy.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.DataSubjectRequestRead;
import eu.royalblackwater.api.dto.DataSubjectRequestResolve;
import eu.royalblackwater.api.dto.PrivacyContactRead;
import eu.royalblackwater.api.dto.PrivacyContactResolve;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.privacy.mapper.PrivacyDtoMapper;
import eu.royalblackwater.api.privacy.repository.PrivacyDataRepository;
import eu.royalblackwater.api.privacy.repository.queries.PrivacyAdministrationQueries;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
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
import static org.springframework.http.HttpStatus.UNPROCESSABLE_CONTENT;

@Service
public class PrivacyAdministrationService {
    private static final Set<String> DECISIONS = Set.of("complete", "reject");
    private static final Pattern SQL_IDENTIFIER = Pattern.compile("[a-z][a-z0-9_]*");
    private final PrivacyDataRepository repository;
    private final PasswordHasher passwords;
    private final AuditService audit;
    private final SecureRandom random;
    private final Clock clock;
    private final PrivacyDtoMapper mapper;

    public PrivacyAdministrationService(PrivacyDataRepository repository, PasswordHasher passwords,
                                        AuditService audit, Clock clock, PrivacyDtoMapper mapper) {
        this.repository = repository;
        this.passwords = passwords;
        this.audit = audit;
        this.random = new SecureRandom();
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<DataSubjectRequestRead> listRequests() {
        return repository.query(PrivacyAdministrationQueries.LIST_REQUESTS_SELECT_01, Map.of()).stream().map(mapper::request).toList();
    }

    @Transactional(readOnly = true)
    public List<PrivacyContactRead> listContacts() {
        return repository.query(PrivacyAdministrationQueries.LIST_CONTACTS_SELECT_01, Map.of()).stream().map(mapper::contact).toList();
    }

    @Transactional
    public PrivacyContactRead resolveContact(long id, PrivacyContactResolve payload, AuthenticatedUser actor) {
        String decision = decision(payload.decision());
        Map<String, Object> row = repository.optional(
                PrivacyAdministrationQueries.RESOLVE_CONTACT_SELECT_01, Map.of("id", id))
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Privacy contact request not found."));
        requirePending(row, "Privacy contact request has already been resolved.");
        repository.update(PrivacyAdministrationQueries.RESOLVE_CONTACT_UPDATE_01, Map.of("status", status(decision), "note", payload.resolutionNote().strip(),
                "actorId", actor.id(), "resolvedAt", now(), "id", id));
        audit.record(actor, "privacy_contact_request", id, decision,
                "Privacy contact request resolved.", List.of("status", "resolution_note"));
        return mapper.contact(repository.required(PrivacyAdministrationQueries.RESOLVE_CONTACT_SELECT_02, Map.of("id", id)));
    }

    @Transactional
    public DataSubjectRequestRead resolveRequest(long id, DataSubjectRequestResolve payload, AuthenticatedUser actor) {
        String decision = decision(payload.decision());
        Map<String, Object> row = repository.optional(PrivacyAdministrationQueries.RESOLVE_REQUEST_SELECT_01, Map.of("id", id)).orElseThrow(
                () -> new ResponseStatusException(NOT_FOUND, "Privacy request not found."));
        requirePending(row, "Privacy request has already been resolved.");
        if ("complete".equals(decision) && "deletion".equals(RowValues.string(row, "request_type"))) {
            pseudonymize(RowValues.longValue(row, "subject_user_id"), row);
        }
        repository.update(PrivacyAdministrationQueries.RESOLVE_REQUEST_UPDATE_01, Map.of("status", status(decision), "note", payload.resolutionNote().strip(),
                "actorId", actor.id(), "resolvedAt", now(), "id", id));
        audit.record(actor, "privacy_request", id, decision,
                "Privacy " + RowValues.string(row, "request_type") + " request resolved.",
                List.of("status", "resolution_note"));
        return mapper.request(repository.required(PrivacyAdministrationQueries.RESOLVE_REQUEST_SELECT_02, Map.of("id", id)));
    }

    private void pseudonymize(long userId, Map<String, Object> userRow) {
        if (RowValues.booleanValue(userRow, "is_bootstrap_admin")) {
            throw new ResponseStatusException(CONFLICT, "The bootstrap administrator cannot be deleted.");
        }
        String oldUsername = RowValues.requiredString(userRow, "subject_username");
        String newUsername = uniqueDeletedUsername(userId);
        String replacementPassword = passwords.hash(randomSecret());
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_DELETE_01, Map.of("id", userId));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_DELETE_02, Map.of("id", userId));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_DELETE_03, Map.of("id", userId));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_DELETE_04, Map.of("id", userId));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_DELETE_05, Map.of("id", userId));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_UPDATE_01, Map.of("id", userId));
        nullNullableUserReferences(userId);
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_UPDATE_02,
                Map.of("username", oldUsername));
        repository.update(PrivacyAdministrationQueries.PSEUDONYMIZE_UPDATE_03, Map.of("username", newUsername, "passwordHash", replacementPassword,
                "updatedAt", now(), "id", userId));
    }

    private void nullNullableUserReferences(long userId) {
        List<Map<String, Object>> references = repository.query(PrivacyAdministrationQueries.NULL_NULLABLE_USER_REFERENCES_SELECT_01, Map.of());
        for (Map<String, Object> reference : references) {
            String table = RowValues.requiredString(reference, "table_name");
            String column = RowValues.requiredString(reference, "column_name");
            if (!SQL_IDENTIFIER.matcher(table).matches() || !SQL_IDENTIFIER.matcher(column).matches()) {
                throw new IllegalStateException("Unsafe user reference metadata encountered.");
            }
            repository.update("update " + table + " set " + column + "=null where " + column + "=:id",
                    Map.of("id", userId));
        }
    }

    private String uniqueDeletedUsername(long userId) {
        for (int attempt = 0; attempt < 5; attempt++) {
            byte[] suffix = new byte[4];
            random.nextBytes(suffix);
            String candidate = "deleted-" + userId + "-" + HexFormat.of().formatHex(suffix);
            if (repository.count(PrivacyAdministrationQueries.UNIQUE_DELETED_USERNAME_SELECT_01, Map.of("username", candidate)) == 0) {
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
            throw new ResponseStatusException(UNPROCESSABLE_CONTENT, "Decision must be complete or reject.");
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


    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
}
