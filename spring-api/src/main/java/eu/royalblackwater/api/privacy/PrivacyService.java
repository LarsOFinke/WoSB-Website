package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.contract.DataSubjectRequestCreate;
import eu.royalblackwater.api.contract.DataSubjectRequestRead;
import eu.royalblackwater.api.contract.PrivacyContactCreate;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.TOO_MANY_REQUESTS;
import static org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY;

@Service
public class PrivacyService {
    private static final Set<String> REQUEST_TYPES = Set.of("correction", "deletion");
    private final JdbcQueryService jdbc;
    private final Clock clock;

    public PrivacyService(JdbcQueryService jdbc, Clock clock) {
        this.jdbc = jdbc;
        this.clock = clock;
    }

    @Transactional
    public Map<String, Object> createContact(PrivacyContactCreate payload, AuthenticatedUser user) {
        String email = normalizedEmail(payload.replyEmail());
        long recent = jdbc.count("""
                select count(*) from privacy_contact_requests
                where reply_email = :email and created_at >= :cutoff
                """, Map.of("email", email, "cutoff", now().minusMinutes(30)));
        if (recent >= 3) {
            throw new ResponseStatusException(TOO_MANY_REQUESTS,
                    "Too many recent privacy messages for this reply address.");
        }
        long id = jdbc.insertReturningId("""
                insert into privacy_contact_requests
                    (user_id, reply_email, subject, message, status, created_at)
                values (:userId, :email, :subject, :message, 'pending', :createdAt)
                returning id
                """, nullableMap(
                        "userId", user == null ? null : user.id(),
                        "email", email,
                        "subject", normalizeWhitespace(payload.subject()),
                        "message", payload.message().strip(),
                        "createdAt", now()));
        return Map.of("id", id, "status", "pending");
    }

    @Transactional(readOnly = true)
    public List<DataSubjectRequestRead> listRequests(int userId) {
        return jdbc.query("""
                select r.id, r.subject_user_id, u.username as subject_username, r.request_type,
                       r.status, r.details, r.resolution_note, r.handled_by_user_id,
                       r.created_at, r.resolved_at
                from data_subject_requests r
                join users u on u.id = r.subject_user_id
                where r.subject_user_id = :userId
                order by r.created_at desc
                limit 100
                """, Map.of("userId", userId)).stream().map(PrivacyService::requestRead).toList();
    }

    @Transactional
    public DataSubjectRequestRead createRequest(AuthenticatedUser user, DataSubjectRequestCreate payload) {
        String type = payload.requestType().strip().toLowerCase(Locale.ROOT);
        if (!REQUEST_TYPES.contains(type)) {
            throw new ResponseStatusException(UNPROCESSABLE_ENTITY, "Unsupported privacy request type.");
        }
        if (user.bootstrapAdmin() && "deletion".equals(type)) {
            throw new ResponseStatusException(CONFLICT,
                    "The bootstrap administrator cannot request account deletion.");
        }
        if ("deletion".equals(type) && !user.username().equals(payload.confirmation())) {
            throw new ResponseStatusException(CONFLICT, "Confirm account deletion with your username.");
        }
        long existing = jdbc.count("""
                select count(*) from data_subject_requests
                where subject_user_id = :userId and request_type = :type and status = 'pending'
                """, Map.of("userId", user.id(), "type", type));
        if (existing > 0) {
            throw new ResponseStatusException(CONFLICT, "An equivalent request is already pending.");
        }
        long id = jdbc.insertReturningId("""
                insert into data_subject_requests
                    (subject_user_id, request_type, status, details, created_at)
                values (:userId, :type, 'pending', :details, :createdAt)
                returning id
                """, nullableMap(
                        "userId", user.id(),
                        "type", type,
                        "details", blankToNull(payload.details()),
                        "createdAt", now()));
        return jdbc.optional("""
                select r.id, r.subject_user_id, u.username as subject_username, r.request_type,
                       r.status, r.details, r.resolution_note, r.handled_by_user_id,
                       r.created_at, r.resolved_at
                from data_subject_requests r join users u on u.id = r.subject_user_id
                where r.id = :id
                """, Map.of("id", id)).map(PrivacyService::requestRead).orElseThrow();
    }

    private String normalizedEmail(String raw) {
        String email = raw.strip().toLowerCase(Locale.ROOT);
        int separator = email.indexOf('@');
        if (separator <= 0 || separator != email.lastIndexOf('@') || separator >= email.length() - 3
                || email.indexOf('.', separator) < separator + 2 || email.chars().anyMatch(Character::isWhitespace)) {
            throw new ResponseStatusException(UNPROCESSABLE_ENTITY, "Enter a valid reply email address.");
        }
        return email;
    }

    private LocalDateTime now() {
        return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
    }

    private static DataSubjectRequestRead requestRead(Map<String, Object> row) {
        return new DataSubjectRequestRead(
                (LocalDateTime) row.get("created_at"),
                (String) row.get("details"),
                number(row.get("handled_by_user_id")),
                ((Number) row.get("id")).longValue(),
                (String) row.get("request_type"),
                (String) row.get("resolution_note"),
                (LocalDateTime) row.get("resolved_at"),
                (String) row.get("status"),
                ((Number) row.get("subject_user_id")).longValue(),
                (String) row.get("subject_username"));
    }

    private static Long number(Object value) {
        return value instanceof Number number ? number.longValue() : null;
    }

    private static String normalizeWhitespace(String value) {
        return String.join(" ", value.strip().split("\\s+"));
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value.strip();
    }

    private static Map<String, Object> nullableMap(Object... values) {
        java.util.LinkedHashMap<String, Object> map = new java.util.LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            map.put(String.valueOf(values[index]), values[index + 1]);
        }
        return map;
    }
}
