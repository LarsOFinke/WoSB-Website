package eu.royalblackwater.api.privacy.service;

import eu.royalblackwater.api.dto.PersonalDataExportRead;
import eu.royalblackwater.api.privacy.mapper.PrivacyDtoMapper;
import eu.royalblackwater.api.privacy.repository.PrivacyDataRepository;
import eu.royalblackwater.api.privacy.repository.queries.PersonalDataExportQueries;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import java.sql.Timestamp;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PersonalDataExportService {
    private static final List<Relation> RELATIONS = List.of(
            new Relation("user_profiles", "user_id"),
            new Relation("user_profile_ship_preferences", "user_id"),
            new Relation("user_profile_role_preferences", "user_id"),
            new Relation("auth_sessions", "user_id"),
            new Relation("registration_requests", "created_user_id"),
            new Relation("cookie_consent_decisions", "user_id"),
            new Relation("fleet_memberships", "user_id"),
            new Relation("stored_files", "owner_id"),
            new Relation("builds", "owner_id"),
            new Relation("build_votes", "user_id"),
            new Relation("guides", "owner_id"),
            new Relation("forum_threads", "owner_id"),
            new Relation("forum_posts", "author_id"),
            new Relation("fleet_events", "owner_id"),
            new Relation("squads", "created_by_id"),
            new Relation("groups", "owner_id"),
            new Relation("group_members", "user_id"),
            new Relation("audit_logs", "actor_user_id"),
            new Relation("data_subject_requests", "subject_user_id"),
            new Relation("privacy_contact_requests", "user_id"));
    private static final Set<String> SECRET_COLUMNS = Set.of("password_hash", "token_hash", "consent_key");
    private final PrivacyDataRepository repository;
    private final Clock clock;
    private final PrivacyDtoMapper mapper;

    public PersonalDataExportService(PrivacyDataRepository repository, Clock clock, PrivacyDtoMapper mapper) {
        this.repository = repository;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public PersonalDataExportRead build(AuthenticatedUser user) {
        Map<String, Object> account = repository.optional(PersonalDataExportQueries.BUILD_SELECT_01, Map.of("userId", user.id())).map(this::safeRow).orElseThrow();
        Map<String, Object> categories = new LinkedHashMap<>();
        for (Relation relation : RELATIONS) {
            verifyMapping(relation);
            List<Map<String, Object>> rows = repository.query(
                    PersonalDataExportQueries.BUILD_SELECT_02 + relation.table() + PersonalDataExportQueries.BUILD_WHERE_01 + relation.ownerColumn() + " = :userId",
                    Map.of("userId", user.id())).stream().map(this::safeRow).toList();
            categories.put(relation.table(), rows);
        }
        return mapper.personalDataExport(
                LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC),
                account,
                categories,
                List.of(
                        "password hashes, session token hashes and consent identifiers",
                        "data belonging to other users",
                        "server secrets and internal cryptographic material"));
    }

    private void verifyMapping(Relation relation) {
        long columns = repository.count(PersonalDataExportQueries.VERIFY_MAPPING_SELECT_01, Map.of("tableName", relation.table(), "columnName", relation.ownerColumn()));
        if (columns != 1) {
            throw new IllegalStateException("Personal data export mapping is stale: "
                    + relation.table() + "." + relation.ownerColumn());
        }
    }

    private Map<String, Object> safeRow(Map<String, Object> row) {
        Map<String, Object> result = new LinkedHashMap<>();
        row.forEach((key, value) -> {
            if (!SECRET_COLUMNS.contains(key)) result.put(key, jsonValue(value));
        });
        return result;
    }

    private static Object jsonValue(Object value) {
        if (value instanceof Timestamp timestamp) return timestamp.toLocalDateTime();
        if (value instanceof LocalDateTime || value instanceof LocalDate) return value;
        if (value instanceof byte[]) return "[binary omitted]";
        return value;
    }

    private record Relation(String table, String ownerColumn) { }
}
