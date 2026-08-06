package eu.royalblackwater.api.privacy.service;

import eu.royalblackwater.api.dto.DataSubjectRequestCreate;
import eu.royalblackwater.api.dto.DataSubjectRequestRead;
import eu.royalblackwater.api.dto.PrivacyContactCreate;
import eu.royalblackwater.api.dto.PrivacyContactReceipt;
import eu.royalblackwater.api.privacy.mapper.PrivacyDtoMapper;
import eu.royalblackwater.api.privacy.repository.PrivacyDataRepository;
import eu.royalblackwater.api.privacy.repository.queries.PrivacyQueries;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
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
    private final PrivacyDataRepository repository;
    private final Clock clock;
    private final PrivacyDtoMapper mapper;

    public PrivacyService(PrivacyDataRepository repository, Clock clock, PrivacyDtoMapper mapper) {
        this.repository = repository;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional
    public PrivacyContactReceipt createContact(PrivacyContactCreate payload, AuthenticatedUser user) {
        String email = normalizedEmail(payload.replyEmail());
        long recent = repository.count(PrivacyQueries.CREATE_CONTACT_SELECT_01, Map.of("email", email, "cutoff", now().minusMinutes(30)));
        if (recent >= 3) {
            throw new ResponseStatusException(TOO_MANY_REQUESTS,
                    "Too many recent privacy messages for this reply address.");
        }
        long id = repository.insertReturningId(PrivacyQueries.CREATE_CONTACT_INSERT_01, nullableMap(
                        "userId", user == null ? null : user.id(),
                        "email", email,
                        "subject", normalizeWhitespace(payload.subject()),
                        "message", payload.message().strip(),
                        "createdAt", now()));
        return mapper.contactReceipt(id);
    }

    @Transactional(readOnly = true)
    public List<DataSubjectRequestRead> listRequests(int userId) {
        return repository.query(PrivacyQueries.LIST_REQUESTS_SELECT_01, Map.of("userId", userId)).stream().map(mapper::request).toList();
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
        long existing = repository.count(PrivacyQueries.CREATE_REQUEST_SELECT_01, Map.of("userId", user.id(), "type", type));
        if (existing > 0) {
            throw new ResponseStatusException(CONFLICT, "An equivalent request is already pending.");
        }
        long id = repository.insertReturningId(PrivacyQueries.CREATE_REQUEST_INSERT_01, nullableMap(
                        "userId", user.id(),
                        "type", type,
                        "details", blankToNull(payload.details()),
                        "createdAt", now()));
        return repository.optional(PrivacyQueries.CREATE_REQUEST_SELECT_02, Map.of("id", id)).map(mapper::request).orElseThrow();
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
