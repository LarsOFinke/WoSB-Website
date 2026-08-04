package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.UserReferenceRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class UserReferenceService {
    private final JdbcQueryService jdbc;

    public UserReferenceService(JdbcQueryService jdbc) {
        this.jdbc = jdbc;
    }

    public UserReferenceRead read(long userId) {
        UserReferenceRead reference = readMany(List.of(userId)).get(userId);
        if (reference == null) {
            throw new java.util.NoSuchElementException("User not found.");
        }
        return reference;
    }

    public Map<Long, UserReferenceRead> readMany(Collection<Long> userIds) {
        List<Long> ids = userIds == null ? List.of() : userIds.stream()
                .filter(java.util.Objects::nonNull)
                .filter(id -> id > 0)
                .distinct()
                .toList();
        if (ids.isEmpty()) {
            return Map.of();
        }
        Map<Long, UserReferenceRead> result = new LinkedHashMap<>();
        for (Map<String, Object> row : jdbc.query("""
                select u.id,coalesce(nullif(up.display_name,''),u.username) display_name
                  from users u
                  left join user_profiles up on up.user_id=u.id
                 where u.id in (:ids)
                 order by u.id
                """, Map.of("ids", ids))) {
            long id = RowValues.longValue(row, "id");
            result.put(id, new UserReferenceRead(RowValues.requiredString(row, "display_name"), id));
        }
        return Map.copyOf(result);
    }
}
